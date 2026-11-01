#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: "askai"
@package: "askai".main.askai.core.support
   @file: shared_instances.py
@created: Tue, 23 Apr 2024
 @author: "<B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: "https://github.com/yorevs/askai")
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from askai.core.support.short_term_memory import ShortTermMemory
from askai.core.support.number_format import compact_count

from askai.__classpath__ import classpath
from askai.core.askai_configs import configs
from askai.core.askai_messages import msg
from askai.core.askai_prompt import prompt
from askai.core.component.cache_service import cache
from askai.core.component.geo_location import geo_location
from askai.core.component.multimedia.recorder import recorder
from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.engine_factory import EngineFactory
from askai.core.support.chat_context import ChatContext, ContextEntry
from askai.core.support.utilities import display_text
from clitt.core.term.terminal import terminal
from clitt.core.tui.line_input.line_input import line_input
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_state
from hspylib.core.tools.text_tools import elide_text
from hspylib.modules.application.version import Version
from hspylib.modules.cli.keyboard import Keyboard
from pathlib import Path
from textwrap import dedent
from typing import Any, Optional

import os


class SharedInstances(metaclass=Singleton):
    """Provides access to shared instances."""

    INSTANCE: "SharedInstances"

    # This is the uuid used in the prompts to indicate that the AI does not know the answer.
    UNCERTAIN_ID: str = "bde6f44d-c1a0-4b0c-bd74-8278e468e50c"

    def __init__(self) -> None:
        self._speech = None
        self._context: ChatContext | None = None
        self._engine: AIEngine | None = None
        self._mode: Any | None = None
        self._memory: ShortTermMemory | None = None
        self._idiom: str = configs.language.idiom
        self._max_iteractions: int = configs.max_iteractions

    @property
    def speech(self):
        from askai.core.speech.service import SpeechService
        if self._speech is None:
            self._speech = SpeechService(configs.stt_engine, configs.tts_engine)
        return self._speech

    def listen(self):
        self.speech.cancel_output()
        _, text = recorder.listen(language=configs.stt_language)
        return text.strip() if text else None

    @property
    def context(self) -> Optional[ChatContext]:
        return self._context

    @context.setter
    def context(self, value: ChatContext) -> None:
        check_state(self._context is None, "Once set, this instance is immutable.")
        self._context = value

    @property
    def engine(self) -> Optional[AIEngine]:
        return self._engine

    @engine.setter
    def engine(self, value: AIEngine) -> None:
        check_state(self._engine is None, "Once set, this instance is immutable.")
        self._engine = value

    @property
    def mode(self) -> Any:
        return self._mode

    @mode.setter
    def mode(self, value: Any) -> None:
        self._mode = value

    def mode_icon(self) -> str:
        return self._mode.icon

    @property
    def nickname(self) -> str:
        return f"%GREEN%{self.mode.icon}  Taius:%NC% "

    @property
    def username(self) -> str:
        return f"%WHITE%  {prompt.user.title()}:%NC% "

    @property
    def nickname_md(self) -> str:
        return f"*{self.mode.icon}  Taius:* "

    @property
    def username_md(self) -> str:
        return f"**  {prompt.user.title()}:** "

    @property
    def idiom(self) -> str:
        return self._idiom

    @property
    def memory(self) -> ShortTermMemory:
        return self.create_memory()

    @property
    def max_iteractions(self) -> int:
        return self._max_iteractions

    @property
    def app_info(self) -> str:
        device_info = f"{recorder.input_device[1]}" if recorder.input_device else ""
        device_info += f", %YELLOW%AUTO-SWAP {'%GREEN%' if recorder.is_auto_swap else '%RED%'}"
        dtm = f" {geo_location.datetime} "
        speech = self.speech.tts
        speak_info = str(configs.tempo) + " @" + getattr(speech, 'voice_name', speech.voice)
        cur_dir = elide_text(str(Path(os.getcwd()).absolute()), 67, "…")
        translator = f"translated by '{msg.translator.name()}'" if configs.language.name.title() != "English" else ""
        eng: AIEngine = shared.engine
        from askai.core.support.context_usage import context_label
        context_info = context_label(eng, msg.t)
        capacity = eng.ai_token_limit()
        capacity_label = compact_count(capacity) if capacity is not None else msg.t("Not reported")
        model_info: str = f"'{eng.ai_model_name()}'%YELLOW% {capacity_label}%GREEN% tokens"
        engine_info: str = f"{eng.ai_name()} - %CYAN%{eng.nickname()} / {model_info}"
        rag_info: str = "%GREEN% " if configs.is_rag else "%RED% "
        assist_info: str = "%GREEN% " if configs.is_assistive else "%RED% "

        tts_reason = getattr(self.speech.tts, 'failure_reason', None)
        tts_details = ("\n           " + msg.t('TTS fallback reason') + ": " + msg.t(tts_reason)) if tts_reason else ""

        # fmt: off
        return dedent(f"""\
            %GREEN%AskAI %YELLOW%v{Version.load(load_dir=classpath.source_path)}%GREEN%
            {dtm.center(80, '=')}
               Language: {configs.language} {translator}
               Location: {' , ' + geo_location.location if configs.ip_api_enabled else '%RED% '} %GREEN%
                 Engine: {engine_info}
                {context_info}
                   Mode: %CYAN%{self.mode}%GREEN%, %YELLOW%RAG: {rag_info}, %YELLOW%Assistive: {assist_info}%GREEN%
                    Dir: {cur_dir}
                     OS: {prompt.os_type}/{prompt.shell}
            {'-' * 80}
             Microphone: %CYAN%{device_info or '%RED%Undetected'} %GREEN%
             TTS Engine: %CYAN%{getattr(self.speech.tts, 'provider_name', configs.tts_engine)} %GREEN%{tts_details}
               Speaking: {' , tempo: ' + speak_info if configs.is_speak else '%RED% '} %GREEN%
            {'.' * 80}
                History: {' ' if configs.is_keep_context else '%RED% '} %GREEN%
                  Debug: {' ' if configs.is_debug else '%RED% '} %GREEN%
                  Cache: {' , ' + msg.t('Response TTL') + ': ' + str(configs.ttl) + ' min' if configs.is_cache else '%RED% '} %GREEN%
            {'=' * 80}%NC%

            """)
        # fmt: on

    def create_engine(self, engine_name: str, model_name: str, mode: Any) -> AIEngine:
        """Create or retrieve an AI engine instance based on the specified engine and model names.
        :param engine_name: The name of the AI engine to create or retrieve.
        :param model_name: The name of the model to use with the AI engine.
        :param mode: The engine routing mode.
        :return: An instance of the AIEngine configured with the specified engine and model.
        """
        if self._engine is None:
            self._engine = EngineFactory.create_engine(engine_name, model_name)
            self._mode = mode
        return self._engine

    def create_context(self, token_limit: int | None) -> ChatContext:
        """Create or retrieve a chat context with the specified token limit.
        :param token_limit: The maximum number of tokens allowed in the chat context.
        :return: An instance of the ChatContext configured with the specified token limit.
        """
        if self._context is None:
            self._context = ChatContext(token_limit, configs.max_short_memory_size)
            if configs.is_keep_context:
                entries: list[str] = cache.read_context()
                for role, content in zip(entries[::2], entries[1::2]):
                    ctx = self._context.store["HISTORY"]
                    ctx.append(ContextEntry(role, content))
        return self._context

    def replace_engine(self, engine, token_limit):
        if self._context is not None:
            self._context.update_token_limit(token_limit)
        self._engine = EngineFactory.activate(engine)

    def create_memory(self, memory_key: str = "chat_history") -> ShortTermMemory:
        """Create or retrieve the conversation window memory.
        :param memory_key: The key used to identify the memory (default is "chat_history").
        :return: An instance of BaseChatMemory associated with the specified memory key.
        """
        if self._memory is None:
            self._memory = ShortTermMemory(configs.max_short_memory_size)
            if configs.is_keep_context:
                entries: list[str] = cache.read_memory()
                for role, content in zip(entries[::2], entries[1::2]):
                    self._memory.add(role, content)
        return self._memory

    def close(self):
        from askai.core.processors.taius import taius

        taius.cancel()
        if self._speech is not None:
            self._speech.close()
        if self._engine is not None:
            self._engine.backend.close()

    def input_text(self, input_prompt: str, placeholder: str | None = None) -> Optional[str]:
        """Prompt the user for input.
        :param input_prompt: The text prompt to display to the user.
        :param placeholder: The placeholder text to display in the input field (optional).
        :return: The user's input as a string, or None if no input is provided.
        """
        ret = None
        while ret is None:
            if (ret := line_input(input_prompt, placeholder)) == Keyboard.VK_CTRL_L:  # Use voice input.
                terminal.cursor.erase_line()
                if spoken_text := self.listen():
                    display_text(f"{self.username}: {spoken_text}")
                ret = spoken_text
            elif ret == Keyboard.VK_CTRL_D:
                return ""

        return ret if not ret or isinstance(ret, str) else ret.val


assert (shared := SharedInstances().INSTANCE) is not None
