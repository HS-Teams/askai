from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from askai.core.support.cache_policy import optional_cache
from transformers import MarianMTModel, MarianTokenizer
from typing import AnyStr

import re


class MarianTranslator(AITranslator):
    """Provides a multilingual offline translation engine using Marian translator.
    Reference: https://marian-nmt.github.io/
    """

    # Specify the model name
    MODEL_NAME = "Helsinki-NLP/opus-mt-en-ROMANCE"

    def __init__(self, from_idiom: Language, to_idiom: Language):
        super().__init__(from_idiom, to_idiom)
        # Load the model and tokenizer
        self._model = MarianMTModel.from_pretrained(self.MODEL_NAME)
        self._tokenizer = MarianTokenizer.from_pretrained(self.MODEL_NAME)

    @optional_cache()
    def _translate_text(self, text: AnyStr, **kwargs) -> str:
        """Translate text from the source language to the target language.
        :param text: Text to translate.
        :return: The translated text.
        """
        kwargs["return_tensors"] = "pt"
        kwargs["padding"] = True

        return self._decode(f">>{self._target_lang.idiom}<<{text}", **kwargs)

    def _decode(self, text, **kwargs) -> str:
        """Wrapper function that is going to provide the translation of the text.
        :param text: The text to be translated.
        :return: The translated text.
        """
        # Replace formatting with placeholders
        text_with_placeholders = re.sub(r"\*\*(.*?)\*\*", r"%BOLD%\1%BOLD%", text)
        text_with_placeholders = re.sub(r"_(.*?)_", r"%ITALIC%\1%ITALIC%", text_with_placeholders)
        text_with_placeholders = re.sub(r"\n", r"%LN%", text_with_placeholders)

        # Prepare the text for the model
        inputs = self._tokenizer.encode(text_with_placeholders, **kwargs)

        # Perform the translation
        translated_text = [self._tokenizer.decode(t) for t in self._model.generate(inputs)][0]

        # Reapply formatting
        translated_text = re.sub(r"% ?BOLD%(.*?)% ?BOLD%", r"**\1**", translated_text)
        translated_text = re.sub(r"% ?ITALIC%(.*?)% ?ITALIC%", r"_\1_", translated_text)
        translated_text = re.sub(r"% ?LN%", r"\n", translated_text)

        return translated_text

    def name(self) -> str:
        return "Marian"
