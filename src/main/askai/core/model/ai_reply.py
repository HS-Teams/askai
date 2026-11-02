#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.engine.model
      @file: ai_reply.py
   @created: Fri, 12 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.enums.verbosity import Verbosity
from dataclasses import dataclass
from rich.console import ConsoleRenderable
from typing import AnyStr, TypeAlias

AnyText: TypeAlias = AnyStr | ConsoleRenderable


@dataclass(frozen=True)
class AIReply:
    """Data class that represents AI replies.
    :param message: The reply message.
    :param is_success: Indicates whether the reply is successful.
    :param is_debug: Indicates whether the reply is for debugging.
    :param verbosity: The verbosity level of the reply.
    :param is_speakable: Indicates whether the reply is speakable.
    """

    message: str
    is_success: bool
    is_debug: bool
    verbosity: Verbosity
    is_speakable: bool
    is_final: bool = False
    is_system: bool = False

    def __str__(self) -> str:
        return self.message

    @staticmethod
    def system(message: str) -> "AIReply":
        """Application status, never narrated as an assistant response."""
        return AIReply(message, True, False, Verbosity.NORMAL, False, is_system=True)

    @staticmethod
    def final(message: str) -> "AIReply":
        """A localized final answer whose Markdown must be preserved by the view."""
        return AIReply(message, True, False, Verbosity.NORMAL, True, is_final=True)

    @staticmethod
    def info(message: AnyText, verbosity: Verbosity = Verbosity.NORMAL, speakable: bool = True) -> "AIReply":
        """Creates an info reply.
        :param message: The reply message.
        :param verbosity: The verbosity level of the reply.
        :param speakable: Indicates whether the reply is speakable.
        :return: An AIReply instance with info settings.
        """
        return AIReply(str(message), True, False, verbosity, speakable)

    @staticmethod
    def detailed(message: AnyText, speakable: bool = False) -> "AIReply":
        """Creates a detailed verbosity reply.
        :param message: The reply message.
        :param speakable: Indicates whether the reply is speakable.
        :return: An AIReply instance with detailed settings.
        """
        return AIReply(str(message), True, False, Verbosity.DETAILED, speakable)

    @staticmethod
    def full(message: AnyText, speakable: bool = False) -> "AIReply":
        """Creates a full verbose reply.
        :param message: The reply message.
        :param speakable: Indicates whether the reply is speakable.
        :return: An AIReply instance with full settings.
        """
        return AIReply(str(message), True, False, Verbosity.FULL, speakable)

    @staticmethod
    def error(message: AnyText) -> "AIReply":
        """Creates an error reply.
        :param message: The reply message.
        :return: An AIReply instance with error settings.
        """
        return AIReply(str(message), False, False, Verbosity.MINIMUM, False)

    @staticmethod
    def debug(message: AnyText) -> "AIReply":
        """Creates a debug reply.
        :param message: The reply message.
        :return: An AIReply instance with debug settings.
        """
        return AIReply(str(message), True, True, Verbosity.NORMAL, False)

    @staticmethod
    def mute(message: AnyText, verbosity: Verbosity = Verbosity.NORMAL) -> "AIReply":
        """Creates a mute reply.
        :param message: The reply message.
        :param verbosity: The verbosity level of the reply.
        :return: An AIReply instance with mute settings.
        """
        return AIReply(str(message), True, False, verbosity, False)

    @property
    def is_error(self) -> bool:
        """Checks if the reply indicates an error.
        :return: True if the reply is not successful, otherwise False.
        """
        return not self.is_success

    def match(self, threshold: "Verbosity" = Verbosity.NORMAL, is_debug: bool = False) -> bool:
        """Checks if the current verbosity level is less than or equal to the given level.
        :param threshold: The verbosity threshold to compare against.
        :param is_debug:
        :return: True if the current level is less than or equal to the given level, otherwise False.
        """
        return (is_debug and self.is_debug) or (not self.is_debug and self.verbosity <= threshold)
