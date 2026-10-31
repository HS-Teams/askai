#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.openai
      @file: openai_engine.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.component.multimedia.recorder import Recorder
from askai.core.speech.contracts import TTSEngine
from askai.core.engine.openai.openai_speech import OpenAISpeech
from askai.core.engine.ai_model import AIModel
from askai.core.engine.ai_vision import AIVision
from askai.core.engine.openai.openai_configs import OpenAiConfigs
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.core.engine.openai.openai_vision import OpenAIVision
from askai.core.model.ai_reply import AIReply
from hspylib.core.preconditions import check_not_none
from openai import APIError, OpenAI
from typing import List, Optional

import logging as log
import os
import tiktoken


class OpenAIEngine:
    """Provide a base class for OpenAI features. This class implements the AIEngine protocol."""

    def __init__(self, model: AIModel = OpenAIModel.GPT_4_O_MINI):
        super().__init__()
        self._model: AIModel = model
        self._configs: OpenAiConfigs = OpenAiConfigs.INSTANCE
        self._api_key: str = os.environ.get("OPENAI_API_KEY")
        self._client = OpenAI(api_key=self._api_key)
        self._vision = OpenAIVision()
        self._speech = OpenAISpeech(self._client, self._configs)

    def __str__(self):
        return f"{self.ai_name()} '{self.nickname()}' '{self._model}'"

    @property
    def url(self) -> str:
        return "https://api.openai.com/v1/chat/completions"

    @property
    def client(self) -> OpenAI:
        return self._client

    def configs(self) -> OpenAiConfigs:
        """Return the engine-specific configurations."""
        return self._configs

    def nickname(self) -> str:
        """Get the AI engine nickname.
        :return: The nickname of the AI engine.
        """
        return "ChatGPT"

    def models(self) -> List[AIModel]:
        """Get the list of available models for the engine.
        :return: A list of available AI models.
        """
        return OpenAIModel.models()

    def speech(self) -> TTSEngine:
        return self._speech

    def vision(self) -> AIVision:
        """Return the engine's vision component.
        :return: The vision component of the engine.
        """
        return self._vision

    def complete(self, messages: list[dict], temperature: float = 0.0, schema: dict | None = None) -> str:
        options = {}
        if schema is not None:
            options["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "askai_response", "strict": True, "schema": schema}}
        response = self.client.chat.completions.create(
            model=self.ai_model_name(), messages=messages, temperature=temperature, **options)
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError("The model returned no text response")
        return content

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = self.client.embeddings.create(model="text-embedding-3-small", input=texts)
        return [item.embedding for item in sorted(result.data, key=lambda item: item.index)]

    def embedding_key(self) -> str:
        return "openai:text-embedding-3-small"

    def ai_name(self) -> str:
        """Get the AI engine name.
        :return: The name of the AI engine.
        """
        return self.__class__.__name__

    def ai_model_name(self) -> str:
        """Get the AI model name.
        :return: The name of the AI model.
        """
        return self._model.model_name()

    def ai_token_limit(self) -> int:
        """Get the AI model token limit.
        :return: The token limit of the AI model.
        """
        return self._model.token_limit()

    def ask(self, chat_context: List[dict], temperature: float = 0.8, top_p: float = 0.0) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        :return: The AI's reply.
        """
        try:
            check_not_none(chat_context)
            log.debug(f"Generating AI answer")
            response = self.client.chat.completions.create(
                model=self.ai_model_name(), messages=chat_context, temperature=temperature, top_p=top_p
            )
            reply = AIReply.info(response.choices[0].message.content)
            log.debug("Response received from LLM: %s", str(reply))
        except APIError as error:
            body: dict = error.body or {"message": "Message not provided"}
            reply = AIReply.error(f"%RED%{error.__class__.__name__} => {body['message']}%NC%")

        return reply

    def speech_to_text(self) -> Optional[str]:
        """Transcribe audio input from the microphone into text.
        :return: The transcribed text or None if transcription fails.
        """
        _, text = Recorder.INSTANCE.listen(language=self._configs.language)
        log.debug(f"Audio transcribed to: {text}")
        return text.strip() if text else None

    def calculate_tokens(self, text: str) -> int:
        """Calculate the number of tokens for the given text.
        :param text: The text for which to calculate tokens.
        :return: The number of tokens in the text.
        """
        encoding: tiktoken.Encoding = tiktoken.encoding_for_model(self._model.model_name())
        tokens: list[int] = encoding.encode(text)
        log.debug(f"Tokens calculated. Text: '{text}'  Tokens: '{tokens}'")
        return len(tokens)
