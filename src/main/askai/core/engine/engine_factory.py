#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine
      @file: engine_factory.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from askai.core.engine.ai_engine import AIEngine
from askai.core.engine.ai_model import AIModel
from askai.core.engine.openai.openai_model import OpenAIModel
from askai.exception.exceptions import NoSuchEngineError
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_not_none


class EngineFactory(metaclass=Singleton):
    """Factory class to create AI engines."""

    INSTANCE: "EngineFactory"

    _ACTIVE_AI_ENGINE: AIEngine | None = None

    @classmethod
    def create_engine(cls, engine_name: str | list[str], engine_model: str | list[str] | None = None) -> AIEngine:
        """Create the suitable AI engine according to the provided engine name.
        :param engine_name: The AI engine name(s).
        :param engine_model: The AI engine model(s).
        :return: An instance of AIEngine.
        """
        engine_name = (engine_name[0] if isinstance(engine_name, list) else engine_name).casefold()
        model_name = engine_model[0] if isinstance(engine_model, list) else engine_model
        match engine_name:
            case "codex" | "claude" | "cursor":
                from askai.core.engine.agent.agent_engine import AgentEngine
                cls._ACTIVE_AI_ENGINE = AgentEngine(engine_name, model_name)
            case "openai":
                from askai.core.engine.openai.openai_engine import OpenAIEngine
                from askai.core.model.api_keys import ApiKeys

                keys = ApiKeys()
                if not keys.has_key("OPENAI_API_KEY"):
                    ApiKeys.prompt()
                    ApiKeys().ensure("OPENAI_API_KEY", "OpenAIEngine")
                model: AIModel = OpenAIModel.of_name(model_name) if model_name else None
                cls._ACTIVE_AI_ENGINE = OpenAIEngine(model or OpenAIModel.GPT_4_O_MINI)
            case "gemini":
                raise NoSuchEngineError("Google 'gemini' is not yet implemented!")
            case _:
                raise NoSuchEngineError(f"Engine name: {engine_name}  model: {engine_model}")

        return cls._ACTIVE_AI_ENGINE

    @classmethod
    def active_ai(cls) -> AIEngine:
        """Get the currently active AI engine.
        :return: The active AI engine.
        :raises TypeError: If no AI engine has been created yet.
        """
        return check_not_none(cls._ACTIVE_AI_ENGINE, "No AI engine has been created yet!")


assert EngineFactory().INSTANCE is not None
