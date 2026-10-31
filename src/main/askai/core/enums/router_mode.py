#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.enums.router_mode
   @file: router_mode.py
@created: Tue, 24 Jun 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from askai.core.askai_configs import configs
from askai.core.askai_messages import msg
from askai.core.processors.ai_processor import AIProcessor
from askai.core.processors.chat import chat
from askai.core.processors.qna import qna
from askai.core.processors.qstring import qstring
from askai.core.processors.rag import rag
from askai.core.processors.taius import taius
from functools import lru_cache
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.tools.dict_tools import get_or_default_by_key
from typing import Optional

import os


class RouterMode(Enumeration):
    """Enumeration of available router modes used to determine the type of response provided to the user. This class
    defines the different modes that the router can operate in, each affecting how answers are generated and delivered.
    """

    # fmt: off

    TAIUS       = "Taius Orchestrator",             "", taius

    QNA         = "Questions & Answers",            "", qna

    QSTRING     = "Non-Interactive",                "", qstring

    RAG         = "Retrieval-Augmented-Generation", "", rag

    CHAT        = "Taius Chat",                     "", chat

    # fmt: on

    @classmethod
    def modes(cls) -> list[str]:
        """Return a list containing all available agent modes.
        :return: A list of available agent modes as strings.
        """
        return RouterMode.names()

    @staticmethod
    @lru_cache
    def default() -> "RouterMode":
        """Return the default routing mode.
        :return: The default RouterMode instance.
        """
        return RouterMode.TAIUS

    @classmethod
    def of_name(cls, name: str) -> "RouterMode":
        """Retrieve the RouterMode instance corresponding to the given name.
        :param name: The name of the router mode to retrieve.
        :return: The RouterMode instance that matches the given name.
        :raises ValueError: If no matching RouterMode is found.
        """
        return cls[name.upper()] if name.casefold() != "default" else cls.default()

    def __str__(self):
        return f"{self.icon}  {self.name}"

    def __eq__(self, other: "RouterMode") -> bool:
        return self.name == other.name

    @property
    def description(self) -> str:
        return self.value[0]

    @property
    def icon(self) -> str:
        return self.value[1]

    @property
    def processor(self) -> AIProcessor:
        return self.value[2]

    @property
    def is_default(self) -> bool:
        return self == RouterMode.default()

    def welcome(self, **kwargs) -> Optional[str]:
        """Generates a welcome message based on the current router mode and optional context.
        :param kwargs: Optional keyword arguments to customize the welcome message.
            - sum_path: The path to the summary context (optional).
            - sum_glob: The glob pattern for the summary files (optional).
        :return: A string containing the welcome message, or None if no message is generated.
        """
        match self:
            case RouterMode.QNA:
                sum_path: str = get_or_default_by_key(kwargs, "sum_path", None)
                sum_glob: str = get_or_default_by_key(kwargs, "sum_glob", None)
                welcome_msg = msg.t(
                    f"{msg.enter_qna()} \n"
                    f"```\nContext:  {sum_path},   {sum_glob} \n```\n"
                    f"`{msg.press_esc_enter()}` \n\n"
                    f"> {msg.qna_welcome()}"
                )
            case RouterMode.RAG:
                welcome_msg = msg.enter_rag()
            case RouterMode.CHAT:
                welcome_msg = msg.enter_chat()
            case _:
                welcome_msg = msg.welcome(os.getenv("USER", "user"))

        return welcome_msg

    def process(self, question: str, **kwargs) -> Optional[str]:
        """Invoke the processor associated with the current mode to handle the given question.
        :param question: The question to be processed.
        :param kwargs: Additional arguments to be passed to the processor.
        :return: The processed response as a string, or None if no response is generated.
        """
        return self.processor.process(question, **kwargs)
