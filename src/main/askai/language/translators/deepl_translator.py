#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.language.argos_translator
      @file: argos_translator.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.__classpath__ import API_KEYS
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from deepl import Translator
from askai.core.support.cache_policy import optional_cache
from typing import AnyStr

import deepl


class DeepLTranslator(AITranslator):
    """Provides a multilingual online translation engine using DeepL translator.
    Reference: https://hnd.www.deepl.com/en/translator
    """

    def __init__(self, source_lang: Language, target_lang: Language):
        super().__init__(source_lang, target_lang)
        self._translator: Translator | None = None

    @optional_cache()
    def _translate_text(self, text: AnyStr, **kwargs) -> str:
        """Translate text from the source language to the target language.
        :param text: Text to translate.
        :return: The translated text.
        """
        # Lazy initialization to allow DEEPL_API_KEY be optional.
        if not self._translator:
            API_KEYS.ensure("DEEPL_API_KEY", "DeepLTranslator")
            self._translator = deepl.Translator(API_KEYS.DEEPL_API_KEY)
        kwargs["preserve_formatting"] = True
        lang = self._from_locale()
        result: deepl.TextResult = self._translator.translate_text(
            text, source_lang=lang[0], target_lang=lang[1], **kwargs
        )
        return str(result)

    def name(self) -> str:
        return "DeepL"

    def _from_locale(self) -> tuple[str, ...]:
        """Convert from locale string to DeepL language.
        Ref:.https://developers.deepl.com/docs/resources/supported-languages
        """
        from_lang: str = self._source_lang.language.upper()
        match self._target_lang:
            case Language.PT_BR:
                to_lang: str = "PT-BR"
            case Language.PT_PT:
                to_lang: str = "PT-PT"
            case Language.EN_GB:
                to_lang: str = "EN-GB"
            case _:
                if self._target_lang.language.casefold() == "en":
                    to_lang: str = "en_US"
                elif self._target_lang.language.casefold() == "zh":
                    to_lang: str = "ZH-HANS"
                else:
                    to_lang: str = self._target_lang.language.upper()
        return from_lang, to_lang.upper()
