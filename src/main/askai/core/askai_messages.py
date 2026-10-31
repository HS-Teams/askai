#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.askai_messages
   @file: askai_messages.py
@created: Fri, 5 Jan 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from askai.core.askai_configs import configs
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from askai.language.detection import detect_language, language_for, prose
from askai.language.translators.deepl_translator import DeepLTranslator
from functools import cached_property, lru_cache
from askai.core.support.cache_policy import optional_cache
from hspylib.core.metaclass.classpath import AnyPath
from hspylib.core.metaclass.singleton import Singleton
from typing import AnyStr

import re


class AskAiMessages(metaclass=Singleton):
    """Provide access to static 'translated' messages."""

    INSTANCE: "AskAiMessages"

    TRANSLATOR: AITranslator = DeepLTranslator

    @staticmethod
    def get_translator(from_lang: Language) -> AITranslator:
        return AskAiMessages._get_translator(from_lang, configs.language)

    @staticmethod
    @lru_cache
    def _get_translator(from_lang: Language, target_lang: Language) -> AITranslator:
        return AskAiMessages.TRANSLATOR(from_lang, target_lang)

    def __init__(self):
        # fmt: off
        self._accurate_responses: list[str] = [
            self.welcome_back()
        ]
        # fmt: on

    @cached_property
    def accurate_responses(self) -> list[str]:
        return self._accurate_responses

    @property
    def translator(self) -> AITranslator:
        return AskAiMessages.get_translator(Language.EN_US)

    def translate(self, text: AnyStr, source_lang: Language | None = Language.EN_US) -> str:
        """Localize app messages, authored in en_US, using the configured language.
        :param text: The text to be translated.
        :param source_lang: Authored source when detection is inconclusive; None for unknown sources.
        :return: The translated text.
        """
        # Avoid translating debug messages.
        if re.match(r"^~~\[DEBUG]~~", str(text), flags=re.IGNORECASE | re.DOTALL | re.MULTILINE):
            return text
        return self._translate(str(text), configs.language, source_lang)

    @optional_cache(maxsize=256)
    def _translate(self, text: str, target_lang: Language, source_hint: Language | None = None) -> str:
        if not any(character.isalpha() for character in prose(text)):
            return text
        detected = detect_language(text)
        source = language_for(detected, source_hint) if detected else source_hint
        if source is None or source.language == target_lang.language:
            return text
        return self._get_translator(source, target_lang).translate(text)

    def translate_response(self, text: str, question: str) -> str:
        """Match the question's language, independently of the interface locale."""
        target_code = detect_language(question)
        if target_code is None:
            return text
        target = language_for(target_code, configs.language)
        from askai.core.speech.narration import translate_narration
        return translate_narration(text, lambda part: self._translate(part, target)) if target else text

    def t(self, text: AnyStr) -> str:
        """Localize app strings whose authored source language is English."""
        return self.translate(text, source_lang=Language.EN_US)

    # Informational

    def welcome(self, username: AnyStr) -> str:
        return f"Welcome back {username}. What can I help with?"

    def wait(self) -> str:
        return "Thinking…"

    def welcome_back(self) -> str:
        return "How may I further assist you ?"

    def listening(self) -> str:
        return "Listening…"

    def dictating(self) -> str:
        return "Dictating…"

    def transcribing(self) -> str:
        return "Processing your voice…"

    def goodbye(self) -> str:
        return "Goodbye, have a nice day !"

    def smile(self, countdown: int) -> str:
        return f"\n  Smile {str(countdown)}…"

    def click(self) -> str:
        return "  !!! Click !!!"

    def look_at_camera(self) -> str:
        return "  Look at the camera…"

    def cmd_success(self, command_line: AnyStr) -> str:
        return f"OK, command `{command_line}` succeeded"

    def searching(self) -> str:
        return f"Searching on the internet…"

    def scrapping(self) -> str:
        return f"Scrapping web site…"

    def summarizing(self, path: AnyPath | None = None) -> str:
        return f"Summarizing documents{' at: ' + str(path) if path else ''}…"

    def summary_succeeded(self, path: AnyPath, glob: str) -> str:
        return f"Summarization of docs at: **{path}/{glob}** succeeded !"

    def enter_qna(self) -> str:
        return "You have *entered* the **Summarization Q & A**"

    def qna_welcome(self) -> str:
        return "  What specific information are you seeking about this content ?"

    def enter_rag(self) -> str:
        return "You have *entered* the **RAG Mode**"

    def enter_chat(self) -> str:
        return "Welcome back, **Sir**! Ready for more 👊 *Epic Adventures* ?"

    def leave_qna(self) -> str:
        return "You have *left* the **Summarization Q & A**"

    def leave_rag(self) -> str:
        return "You have *left* the **RAG Mode**"

    def leave_chat(self) -> str:
        return f"Bye, **Sir**! If you need anything else, ⚡ **Just let me Rock**  ⚡ !"

    def press_esc_enter(self) -> str:
        return "Type [exit] to exit Q & A mode"

    def device_switch(self, device_info: AnyStr) -> str:
        return f"\nSwitching to Audio Input device: `{device_info}`\n"

    # Debug messages

    def photo_captured(self, photo: AnyStr) -> str:
        return f"~~[DEBUG]~~ WebCam photo captured: `{photo}`"

    def screenshot_saved(self, screenshot: AnyStr) -> str:
        return f"~~[DEBUG]~~ Screenshot saved: `{screenshot}`"

    def executing(self, command_line: AnyStr) -> str:
        return f"~~[DEBUG]~~ Executing: `{command_line}`…"

    def analysis(self, result: AnyStr) -> str:
        return f"~~[DEBUG]~~ Analysis result => {result}"

    def assert_acc(self, status: AnyStr, details: AnyStr) -> str:
        match status.casefold():
            case "red":
                cl = "%RED%"
            case "yellow":
                cl = "%YELLOW%"
            case "green":
                cl = "%GREEN%"
            case "blue":
                cl = "%BLUE%"
            case _:
                cl = ""
        return f"~~[DEBUG]~~ Accuracy result => {cl}{status}:%NC% {details}"

    def x_reference(self, pathname: AnyPath) -> str:
        return f"~~[DEBUG]~~ Resolving X-References: `{pathname}`…"

    def describe_image(self, image_path: AnyPath) -> str:
        return f"~~[DEBUG]~~ Describing image: `{image_path}`…"

    def parsing_caption(self) -> str:
        return f"~~[DEBUG]~~ Parsing caption…"

    def task(self, task: AnyStr) -> str:
        return f"~~[DEBUG]~~ > `Task:` {task}"

    def final_query(self, query: AnyStr) -> str:
        return f"~~[DEBUG]~~ > Final query: `{query}`"

    def refine_answer(self, answer: AnyStr) -> str:
        return f"~~[DEBUG]~~ > Refining answer: `{answer}`"

    def no_caption(self) -> str:
        return "No caption available"

    def no_good_result(self) -> str:
        return "The search did not bring any good result"

    # Warnings and alerts

    def no_output(self, source: AnyStr) -> str:
        return f"The {source} didn't produce an output !"

    def access_grant(self) -> str:
        return "Do you approve executing this command on you terminal (~~yes/[no]~~)?"

    def sorry_retry(self) -> str:
        return "Sorry, I failed to respond. Let me try again."

    # Failures

    def no_query_string(self) -> str:
        return "No query string was provided in non-interactive mode !"

    def invalid_response(self, response_text: AnyStr) -> str:
        return f"Invalid query response/type => '{response_text}' !"

    def invalid_command(self, response_text: AnyStr) -> str:
        return f"Invalid **AskAI** command => '{response_text}' !"

    def cmd_no_exist(self, command: AnyStr) -> str:
        return f"Command: `{command}' does not exist !"

    def cmd_failed(self, cmd_line: AnyStr, error_msg: AnyStr) -> str:
        return f"Command: `{cmd_line}' failed to execute -> {error_msg}!"

    def camera_not_open(self) -> str:
        return "Camera is not open, or unauthorized!"

    def missing_package(self, err: ImportError) -> str:
        return f"Unable to summarize => {str(err)}' !"

    def summary_not_possible(self, err: BaseException = None) -> str:
        return f"Summarization was not possible {'=> ' + str(err) if err else ''}!"

    def intelligible(self, reason: AnyStr) -> str:
        return f"Your speech was not intelligible => '{reason}' !"

    def impossible(self, reason: AnyStr) -> str:
        return f"Impossible to fulfill your request => `{reason}` !"

    def timeout(self, reason: AnyStr) -> str:
        return f"Time out while {reason} !"

    def llm_error(self, error: AnyStr) -> str:
        return f"**LLM** failed to reply: {error} !"

    def fail_to_search(self, error: AnyStr) -> str:
        return f"'Internet Search' failed: {error} !"

    def too_many_actions(self) -> AnyStr:
        return "Failed to complete the request => 'Max chained actions reached' !"

    def unprocessable(self, reason: AnyStr) -> str:
        return f"Sorry, {reason}"

    def quote_exceeded(self) -> str:
        return (
            f"Oops! Looks like you have reached your quota limit. You can add credits at: "
            f"https://platform.openai.com/settings/organization/billing/overview"
        )

    def interruption_requested(self, reason: str) -> str:
        return f" Interrupting execution => {reason}…"

    def terminate_requested(self, reason: str) -> str:
        return f" Terminating execution => {reason}. Exiting…"


assert (msg := AskAiMessages().INSTANCE) is not None
