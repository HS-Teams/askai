#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.tui.app_suggester
      @file: app_suggester.py
   @created: Wed, 19 Jun 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.cli.suggestions import input_suggestion
from askai.core.commander.commander import command_suggestions
from askai.core.component.cache_service import cache
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from textual.suggester import Suggester
from typing import Optional


class InputSuggester(Suggester):
    """Implement a list-based Input suggester."""

    def __init__(self, *, case_sensitive: bool = True) -> None:
        super().__init__(use_cache=False, case_sensitive=case_sensitive)
        KeyboardInput.preload_history(cache.load_input_history(command_suggestions()))
        self._suggestions: list[str] = KeyboardInput.history()
        self._for_comparison: list[str] = list(
            self._suggestions if self.case_sensitive else [suggestion.casefold() for suggestion in self._suggestions]
        )

    async def suggestions(self) -> list[str]:
        """Return all available suggestions."""
        return list(set(self._suggestions))

    async def add_suggestion(self, value: str) -> None:
        """Add a new suggestion."""
        if value not in self._suggestions and value not in self._for_comparison:
            self._suggestions.append(value)
            self._for_comparison.append(value if self.case_sensitive else value.casefold())

    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get a suggestion from the list."""
        return input_suggestion(value, self._suggestions, self.case_sensitive)
