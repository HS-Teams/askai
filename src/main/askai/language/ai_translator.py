#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.language.argos_translator
      @file: translator.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from abc import ABC
from askai.core.askai_events import events
from askai.core.model.ai_reply import AIReply
from askai.language.language import Language
from askai.language.detection import detect_language, prose
from typing import AnyStr

import re


class AITranslator(ABC):
    """Provides a base class for multilingual offline translation engines. Various implementations can be used."""

    def __init__(self, source_lang: Language, target_lang: Language):
        self._source_lang: Language = source_lang
        self._target_lang: Language = target_lang

    def translate(self, text: AnyStr) -> str:
        """Translates text excluding the parts enclosed in [TAG]...[/TAG] and %TAG%...%TAG% formatting.
        :param text: The input text with [TAG]...[/TAG] and %TAG%...%TAG% formatting.
        :returns str: The translated text with original tags preserved.
        """
        if self._source_lang.language == self._target_lang.language:
            return text
        content = prose(str(text))
        if not any(character.isalpha() for character in content):
            return text
        source = detect_language(str(text)) or self._source_lang.language
        if source == self._target_lang.language:
            return text

        # Regex to match [TAG]..[/TAG], %TAG%..%/TAG%, "..", and '..'
        tag_pattern = re.compile(
            r"(```[\s\S]*?```|`[^`]*`|https?://[^\s)]+|\[/?\w+]|%/?\w+%|[\"']\w+[\"'])",
            re.IGNORECASE,
        )
        parts = tag_pattern.split(text)  # Split the text into parts: tags and non-tags
        texts_to_translate = []
        indices = []
        # Collect texts to translate
        for i, part in enumerate(parts):
            if not tag_pattern.fullmatch(part) and part.strip() != "":
                texts_to_translate.append(part)
                indices.append(i)

        try:
            # Perform batch translation
            translated_texts: list[str] = list(map(self._translate_text, texts_to_translate))
        except Exception as err:
            events.reply.emit(reply=AIReply.debug(f"Error during batch translation: {err}"))
            return text

        # Replace translated texts in the parts list
        for idx, translated in zip(indices, translated_texts):
            parts[idx] = translated

        # Reassemble the translated text with tags
        translated_text = "".join(parts)

        return translated_text

    def _translate_text(self, text: AnyStr, **kwargs) -> str:
        """Translate text from the source language to the target language.
        :param text: Text to translate.
        :return: The translated text.
        """
        ...

    def name(self) -> str:
        """Return the translator name or model.
        :return: The name or model of the translator.
        """
        ...

    def usage(self):
        from askai.core.support.usage import Usage

        return [Usage(self.name(), '-')]
