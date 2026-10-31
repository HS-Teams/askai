#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core
      @file: askai.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.__classpath__ import classpath
from askai.core.commander.command_args import command_args
from askai.core.askai_configs import configs
from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.askai_settings import settings
from askai.core.commander.commander import ask_commander, RE_ASKAI_CMD
from askai.core.component.cache_service import cache, CACHE_DIR
from askai.core.engine.ai_engine import AIEngine
from askai.core.enums.router_mode import RouterMode
from askai.core.model.ai_reply import AIReply
from askai.core.processors.ai_processor import AIProcessor
from askai.core.support.chat_context import ChatContext
from askai.core.support.shared_instances import shared
from askai.core.support.utilities import read_stdin
from askai.exception.exceptions import *
from askai.tui.app_icons import AppIcons
from click import UsageError
from clitt.core.term.terminal import terminal
from hspylib.core.enums.charset import Charset
from hspylib.core.tools.commons import file_is_not_empty, is_debugging
from hspylib.core.zoned_datetime import DATE_FORMAT, now, TIME_FORMAT
from hspylib.modules.application.exit_status import ExitStatus
from pydantic import ValidationError
from openai import RateLimitError
from pathlib import Path
from typing import Any, Optional

import logging as log
import os
import re
import sys
import threading


class AskAi:
    """The AskAI core functionalities."""

    SOURCE_DIR: Path = classpath.source_path

    RESOURCE_DIR: Path = classpath.resource_path

    SPLASH: str = classpath.get_resource("splash.txt").read_text(encoding=Charset.UTF_8.val)

    @staticmethod
    def _abort():
        """Abort the execution and exit."""
        terminal.restore()
        sys.exit(ExitStatus.FAILED.val)

    def __init__(
        self, speak: bool, debug: bool, cacheable: bool, tempo: int, engine_name: str, model_name: str, mode: RouterMode
    ):

        configs.is_debug = is_debugging() or debug
        configs.is_speak = speak
        configs.is_cache = cacheable
        configs.tempo = tempo

        self._session_id = now("%Y%m%d")[:8]
        self._engine: AIEngine = shared.create_engine(engine_name, model_name, mode)
        configs.engine = engine_name
        configs.agent = engine_name
        if model_name:
            configs.model = model_name
        self._context: ChatContext = shared.create_context(self._engine.ai_token_limit())
        self._mode: RouterMode = shared.mode
        self._console_path = Path(f"{CACHE_DIR}/askai-{self.session_id}.md")
        self._query_prompt: str | None = None
        self._abort_count: int = 0

        if not self._console_path.exists():
            self._console_path.touch()

    def __str__(self) -> str:
        return shared.app_info

    @property
    def engine(self) -> AIEngine:
        return self._engine

    @property
    def context(self) -> ChatContext:
        return self._context

    @property
    def mode(self) -> RouterMode:
        return shared.mode

    @mode.setter
    def mode(self, value: RouterMode):
        shared.mode = value

    @property
    def query_prompt(self) -> str:
        return self._query_prompt

    @property
    def console_path(self) -> Path:
        return self._console_path

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def app_settings(self) -> list[tuple[str, ...]]:
        all_settings: list[tuple[str, ...]] = [("UUID", "Setting", "Value")]
        for s in settings.settings.search():
            r: tuple[str, ...] = str(s.identity["uuid"]), str(s.name), str(s.value)
            all_settings.append(r)
        return all_settings

    def abort(self, signals: Any | None = None, frame: Any | None = None) -> None:
        """Hook the SIGINT signal for cleanup or execution interruption. If two signals arrive within 1 second,
        abort the application execution.
        :param signals: Signal number from the operating system.
        :param frame: Current stack frame at the time of signal interruption.
        """
        log.warning(f"User interrupted: signals: {signals}  frame: {frame}")
        shared.speech.cancel_output()
        self._abort_count += 1
        if self._abort_count > 1:
            events.reply.emit(reply=AIReply.error(f"\n{msg.terminate_requested('User aborted [ctrl+c]')}"))
            log.warning(f"User aborted. Exiting…")
            self._abort()
        if hasattr(self.mode.processor, "cancel"):
            self.mode.processor.cancel()
        events.abort.emit(message="User interrupted [ctrl+c]")
        threading.Timer(1, lambda: setattr(self, "_abort_count", 0)).start()

    def run(self) -> None:
        """Run the application."""
        ...

    def ask_and_reply(self, question: str) -> tuple[bool, Optional[str]]:
        """Ask the specified question to the AI and provide the reply.
        :param question: The question to ask the AI engine.
        :return: A tuple containing a boolean indicating success or failure, and the AI's reply as an optional string.
        """
        shared.speech.cancel_output()
        status: bool = True
        output: str | None = None
        processor: AIProcessor = self.mode.processor
        assert isinstance(processor, AIProcessor)

        try:
            if command := re.search(RE_ASKAI_CMD, question):
                try:
                    args = command_args(command)
                except ValueError as error:
                    raise UsageError(str(error)) from error
                ask_commander(args, standalone_mode=False)
                return True, None
            shared.context.push("HISTORY", question)
            if not getattr(processor, "cacheable", True) or not (output := cache.read_reply(question)):
                log.debug('Response not found for "%s" in cache. Querying from %s.', question, self.engine.nickname())
                events.reply.emit(reply=AIReply.detailed(msg.wait()))
                if output := processor.process(question, context=read_stdin(), query_prompt=self._query_prompt):
                    events.reply.emit(reply=AIReply.final(output))
            else:
                log.debug("Reply found for '%s' in cache.", question)
                events.reply.emit(reply=AIReply.final(output))
        except (RuntimeError, NotImplementedError, ImpossibleQuery, DocumentsNotFound) as err:
            events.reply.emit(reply=AIReply.error(err))
        except (MaxInteractionsReached, InaccurateResponse, ValidationError) as err:
            events.reply.emit(reply=AIReply.error(msg.unprocessable(err)))
        except UsageError as err:
            events.reply.emit(reply=AIReply.error(msg.invalid_command(err)))
        except IntelligibleAudioError as err:
            events.reply.emit(reply=AIReply.error(msg.intelligible(err)))
        except RateLimitError:
            events.reply.emit(reply=AIReply.error(msg.quote_exceeded()))
            status = False
        except TerminatingQuery:
            self._reply(AIReply.info(msg.goodbye()))
            status = False
        finally:
            if output:
                shared.context.push("HISTORY", output, "assistant")
                shared.context.set("LAST_REPLY", output, "assistant")
                if not getattr(processor, "cacheable", True):
                    shared.context.save()

        return status, output

    def _create_console_file(self, overwrite: bool = True) -> None:
        """Create a Markdown-formatted console file.
        :param overwrite: Whether to overwrite the existing file if it already exists (default is True).
        """
        is_new: bool = not file_is_not_empty(str(self.console_path)) or overwrite
        with open(self.console_path, "w" if overwrite else "a", encoding=Charset.UTF_8.val) as f_console:
            f_console.write(
                f"{'---' + os.linesep * 2 if not is_new else ''}"
                f"{'# ' + now(DATE_FORMAT) + os.linesep * 2 if is_new else ''}"
                f"## {AppIcons.STARTED} {now(TIME_FORMAT)}\n\n"
            )
            f_console.flush()

    def _reply(self, reply: AIReply) -> None:
        """Reply to the user with the AI-generated response.
        :param reply: The reply message to send as a reply to the user.
        """
        ...

    def _reply_error(self, reply: AIReply) -> None:
        """Reply to the user with an AI-generated error message or system error.
        :param reply: The error reply message to be displayed to the user.
        """
        ...
