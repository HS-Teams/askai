#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.model
      @file: ai_engine.py
   @created: Fri, 5 May 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_configs import AskAiConfigs
from askai.core.engine.ai_model import AIModel
from askai.core.engine.ai_vision import AIVision
from askai.core.model.ai_reply import AIReply
from typing import Optional, Protocol


class AIEngine(Protocol):
    """Provide an interface for AI engines."""

    def configs(self) -> AskAiConfigs:
        """Return the engine-specific configurations."""
        ...

    def nickname(self) -> str:
        """Get the AI engine nickname.
        :return: The nickname of the AI engine.
        """
        ...

    def models(self) -> list[AIModel]:
        """Get the list of available models for the engine.
        :return: A list of available AI models.
        """
        ...

    def vision(self) -> AIVision:
        """Return the engine's vision component.
        :return: The vision component of the engine.
        """
        ...

    def complete(self, messages: list[dict], temperature: float = 0.0, schema: dict | None = None) -> str:
        """Generate text, optionally constrained by a JSON schema; propagate provider errors."""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed text in this provider's declared embedding space."""
        ...

    def embedding_key(self) -> str:
        """Identify the embedding space used by persisted vector stores."""
        ...

    def ai_name(self) -> str:
        """Get the AI engine name.
        :return: The name of the AI engine.
        """
        ...

    def ai_model_name(self) -> str:
        """Get the AI model name.
        :return: The name of the AI model.
        """
        ...

    def ai_token_limit(self) -> int:
        """Get the AI model token limit.
        :return: The token limit of the AI model.
        """
        ...

    def ask(self, chat_context: list[dict], temperature: float = 0.8, top_p: float = 0.0) -> AIReply:
        """Ask AI assistance for the given question and expect a response.
        :param chat_context: The chat history or context.
        :param temperature: The model engine temperature.
        :param top_p: The model engine top_p.
        :return: The AI's reply.
        """
        ...

    def calculate_tokens(self, text: str) -> int:
        """Calculate the number of tokens for the given text.
        :param text: The text for which to calculate tokens.
        :return: The number of tokens in the text.
        """
        ...
