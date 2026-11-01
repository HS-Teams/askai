#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core
   @file: askai_cli.py
@created: Fri, 9 Aug 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""

from askai.core.askai import AskAi
from askai.core.askai_configs import configs
from askai.core.askai_events import *
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.commander.commander import command_suggestions
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.component.multimedia.audio_player import player
from askai.core.component.multimedia.recorder import recorder
from askai.core.component.scheduler import scheduler
from askai.core.enums.router_mode import RouterMode
from askai.core.model.ai_reply import AIReply
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import display_text
from askai.tui.app_icons import AppIcons
from clitt.core.term.cursor import cursor
from clitt.core.term.screen import screen
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import console_out
from hspylib.core.zoned_datetime import now, TIME_FORMAT
from hspylib.modules.eventbus.event import Event
from pathlib import Path
from rich.progress import Progress
from textwrap import indent
from threading import Thread
from typing import Optional

import logging as log
import nltk
import os
import pause
import signal


class AskAiCli(AskAi):
    """The AskAI CLI application."""

    def __init__(
        self,
        speak: bool,
        debug: bool,
        cacheable: bool,
        tempo: int,
        query_prompt: str | None,
        engine_name: str,
        model_name: str,
        query_string: str | None,
        mode: RouterMode,
    ):
        super().__init__(speak, debug, cacheable, tempo, engine_name, model_name, mode)
        self._listening_indicator = None
        self._ready: bool = False
        self._query_prompt: str | None = query_prompt
        self._query_string: str | None = query_string
        from askai.core.processors.taius import taius
        from askai.cli.agent_interaction import AgentInteraction
        from askai.cli.agent_progress import AgentProgress
        from askai.cli.confirmation import Confirmation, show_confirmation, read_confirmation_key
        from askai.core.support.text_formatter import text_formatter as tf

        interact = AgentInteraction(
            lambda placeholder: shared.input_text(shared.username, placeholder),
            lambda text: display_text(text, shared.nickname, markdown=False),
            translate=msg.translate,
            confirm=Confirmation(
                read_confirmation_key,
                lambda message, grants=(): show_confirmation(tf.console, message, msg.translate, grants),
                translate=msg.translate,
                echo=lambda text: display_text(text, shared.username, markdown=False),
            ),
        )
        self._agent_progress = AgentProgress(tf.console, interact)
        taius.interact = self._agent_progress.interact
        taius.emit = self._agent_event
        self._startup()

    def run(self) -> None:
        """Run the application."""
        signal.signal(signal.SIGINT, self.abort)  # Handle Ctrl+C
        signal.signal(signal.SIGTERM, self.abort)  # Handle termination requests
        signal.signal(signal.SIGHUP, self.abort)  # Handle terminal hangup
        while question := (self._query_string or self._input()):
            status, output = self.ask_and_reply(question)
            if not status:
                question = None
                break
            elif output:
                if getattr(self.mode.processor, "cacheable", True):
                    cache.save_reply(self._reply_cache_key, output)
                cache.save_input_history()
                # FIXME This is only writing the final answer to the markdown file.
                with open(self.console_path, "a+", encoding=Charset.UTF_8.val) as f_console:
                    f_console.write(f"{shared.username_md}{question}\n\n")
                    f_console.write(f"{shared.nickname_md}{output}\n\n")
                    f_console.flush()
            if not configs.is_interactive:
                break
        if question == "":
            self._reply(AIReply.info(msg.goodbye()))
        display_text("", markdown=False)

    def _reply(self, reply: AIReply) -> None:
        """Reply to the user with the AI-generated response.
        :param reply: The reply message to send as a reply to the user.
        """
        if not reply:
            return
        from askai.cli.answer_renderer import render_answer
        from askai.cli.speech_renderer import stream_answer
        from askai.core.support.text_formatter import text_formatter

        text = reply.message if reply.is_final else msg.translate(reply.message)
        from askai.core.speech.narration import parse_narration
        from askai.core.speech.presentation import format_narration
        narration = parse_narration(text) if reply.is_final else None
        spoken = narration.spoken if narration else text
        text = format_narration(narration) if narration else text
        label = f"{self.mode.icon} Taius"
        render = lambda: render_answer(text_formatter.console, text, label) if reply.is_final else display_text(text, shared.nickname)
        if configs.is_speak and reply.is_speakable and spoken:
            def failed(error):
                render()
                events.reply.emit(reply=AIReply.error(str(error)))
            shared.speech.speak(
                spoken, failed,
                present=lambda duration, cancelled: stream_answer(text_formatter.console, text, label, duration, cancelled, narration),
                wait=True,
            )
        else:
            render()

    def _reply_error(self, reply: AIReply) -> None:
        """Reply to the user with an AI-generated error message or system error.
        :param reply: The error reply message to be displayed to the user.
        """
        if reply and (text := msg.translate(reply.message)):
            log.error(reply.message if configs.is_keep_context else "AskAI request failed (history disabled)")
            if configs.is_speak and reply.is_speakable:
                display_text(f"Error: {text}", f"{shared.nickname}")
                shared.speech.speak(f"Error: {text}", lambda error: events.reply.emit(reply=AIReply.error(str(error))))
            else:
                display_text(f"%RED%Error: {text}%NC%", f"{shared.nickname}")

    def _input(self) -> Optional[str]:
        """Read the user input from stdin.
        :return: The user's input as a string, or None if no input is provided.
        """
        return shared.input_text(f"{shared.username}", f"{msg.t('Message')} {self.engine.nickname()}", allow_voice=True)

    def _agent_event(self, event) -> None:
        if event.kind == "reasoning_summary":
            if configs.is_debug:
                events.reply.emit(reply=AIReply.debug("Debug · Codex: " + event.data["text"]))
            return
        self._agent_progress.emit(event)
        if event.kind != "initial_commentary":
            return
        from askai.cli.answer_renderer import render_answer
        from askai.core.support.text_formatter import text_formatter

        text = event.data["text"]
        self._agent_progress.present(lambda: render_answer(text_formatter.console, text, f"{self.mode.icon} Taius"))
        if configs.is_speak:
            shared.speech.speak(text, lambda error: log.warning("Initial commentary TTS failed: %s", error), wait=False, immediate=True)

    def _cb_tts_fallback(self, ev: Event) -> None:
        if not self._ready:
            self._pending_tts_fallback = ev
            return
        message = msg.t(
            f"TTS switched from {ev.args.provider} to Ollama. Reason: {ev.args.reason}. "
            "The configured default was not changed."
        )
        display_text(f"%YELLOW%{message}%NC%", "⚠ " + msg.t("Warning") + " · TTS: ", markdown=False)

    def _cb_voice_input(self, ev: Event) -> None:
        from askai.cli.prompt_input import request_voice
        if not request_voice():
            log.debug('Gesture voice input ignored: no empty question prompt is active')

    def _cb_reply_event(self, ev: Event) -> None:
        from askai.cli.prompt_input import present
        present(lambda: self._display_reply_event(ev))

    def _display_reply_event(self, ev: Event) -> None:
        """Callback to handle reply events.
        :param ev: The event object representing the reply event.
        """
        reply: AIReply
        if reply := ev.args.reply:
            if reply.is_error:
                self._reply_error(reply)
            else:
                if ev.args.reply.match(configs.verbosity, configs.is_debug):
                    if ev.args.erase_last:
                        cursor.erase_line()
                    self._reply(reply)

    def _cb_mode_changed_event(self, ev: Event) -> None:
        """Callback to handle mode change events.
        :param ev: The event object representing the mode change.
        """
        self.mode: RouterMode = RouterMode.of_name(ev.args.mode)
        if self.mode == RouterMode.QNA:
            welcome_msg = self.mode.welcome(sum_path=ev.args.sum_path, sum_glob=ev.args.glob)
        else:
            welcome_msg = self.mode.welcome()

        events.reply.emit(reply=AIReply.info(welcome_msg or msg.welcome(prompt.user.title())))

    def _cb_mic_listening_event(self, ev: Event) -> None:
        """Callback to handle microphone listening events.
        :param ev: The event object representing the microphone listening event.
        """
        from askai.cli.listening_indicator import ListeningIndicator
        from askai.core.support.text_formatter import text_formatter

        if self._listening_indicator is None:
            self._listening_indicator = ListeningIndicator(text_formatter.console, msg.translate)
        self._listening_indicator.update(ev.args.listening, ev.args.text)

    def _cb_device_changed_event(self, ev: Event) -> None:
        """Callback to handle audio input device change events.
        :param ev: The event object representing the device change.
        """
        from rich.text import Text
        from askai.core.support.text_formatter import text_formatter
        from askai.cli.prompt_input import present

        notice = Text(msg.t("System") + ": ", style="bold yellow")
        notice.append(msg.translate(msg.device_switch(str(ev.args.device))).strip(), style="default")
        present(lambda: text_formatter.console.print(notice))

    def _splash(self, interval: int = 250) -> None:
        """Display the AskAI splash screen until the system is fully started and ready. This method shows the splash
        screen during the startup process and hides it once the system is ready.
        :param interval: The interval in milliseconds for polling the startup status (default is 250 ms).
        """
        screen.clear()
        console_out.print(indent(self.SPLASH, " " * 13))
        while not self._ready:
            pause.milliseconds(interval)
        screen.clear()

    def _startup(self) -> None:
        """Initialize the application components."""
        progress: Progress = Progress()
        # List of tasks for progress tracking
        tasks = [
            "Downloading nltk data",
            "Loading input history",
            "Starting scheduler",
            "Setting up recorder",
            "Checking speech engine",
            "Preparing document index",
            "Starting player delay",
            "Finalizing startup",
        ]
        # Start and manage the progress bar
        askai_bus = AskAiEvents.bus(ASKAI_BUS_NAME)
        askai_bus.subscribe(VOICE_INPUT_EVENT, self._cb_voice_input)
        askai_bus.subscribe(REPLY_EVENT, self._cb_reply_event)
        askai_bus.subscribe(TTS_FALLBACK_EVENT, self._cb_tts_fallback)
        if configs.is_interactive:
            splash_thread: Thread = Thread(daemon=True, target=self._splash)
            splash_thread.start()
            task = progress.add_task(f'[green] {msg.t("Starting up...")}', total=len(tasks))
            with progress:
                os.chdir(Path.home())
                from askai.core.support.startup import run_startup_tasks
                from askai.core.processors.rag import rag

                cache.cache_enable = configs.is_cache
                try:
                    results = run_startup_tasks({
                        "Downloading nltk data": lambda: nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR),
                        "Loading input history": lambda: cache.load_input_history(command_suggestions()),
                        "Checking speech engine": shared.speech.initialize_tts,
                        "Preparing document index": rag.prepare,
                    }, lambda name: progress.update(task, advance=1, description=f"[green] {msg.t(name)}"))
                except BaseException:
                    self._ready = True
                    splash_thread.join()
                    raise
                KeyboardInput.preload_history(results["Loading input history"])
                progress.update(task, advance=1, description=f'[green] {msg.t("Starting scheduler")}')
                scheduler.start()
                progress.update(task, advance=1, description=f'[green] {msg.t("Setting up recorder")}')
                recorder.setup()
                progress.update(task, advance=1, description=f'[green] {msg.t("Starting player delay")}')
                player.start_delay()
                progress.update(task, advance=1, description=f'[green] {msg.t("Finalizing startup")}')
            self._ready = True
            splash_thread.join()
            askai_bus.subscribe(MIC_LISTENING_EVENT, self._cb_mic_listening_event)
            askai_bus.subscribe(DEVICE_CHANGED_EVENT, self._cb_device_changed_event)
            askai_bus.subscribe(MODE_CHANGED_EVENT, self._cb_mode_changed_event)
            display_text(str(self), markdown=False)
            pending = getattr(self, "_pending_tts_fallback", None)
            if pending is not None:
                self._pending_tts_fallback = None
                self._cb_tts_fallback(pending)
            self._reply(AIReply.info(self.mode.welcome()))
        elif configs.is_speak:
            shared.speech.initialize_tts()
            nltk.download("averaged_perceptron_tagger", quiet=True, download_dir=CACHE_DIR)
            recorder.setup()
            player.start_delay()
        # Register the startup
        with open(self.console_path, "a+", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(f"\n\n## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n")
            f_console.flush()
        log.info("AskAI is ready to use!")
