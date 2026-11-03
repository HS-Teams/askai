#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.commander.settings_cmd
      @file: settings_cmd.py
   @created: Thu, 25 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from abc import ABC
from askai.core.askai_configs import configs
from askai.core.askai_settings import settings
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import display_text
from hspylib.core.tools.commons import sysout
from setman.settings.settings_entry import SettingsEntry
from typing import Any, Optional


class SettingsCmd(ABC):
    """Provides settings manipulation command functionalities."""

    @staticmethod
    def list(filters: str | None = None) -> None:
        """List all settings, optionally matching filters."""
        if all_settings := settings.search(f"*{filters}*"):
            sysout(all_settings + "\n")
        else:
            sysout(f"\n%RED%-=- No settings found! -=-%NC%\n")
        display_text(f"> Hint: Type: '/settings set \\<number|settings_name\\> \\<value\\>' to set.")

    @staticmethod
    def set(name: str, value: Any, *, announce: bool = True) -> None:
        """Set a setting value.
        :param name: The name of the setting to update or create.
        :param value: The value to assign to the setting.
        """
        all_settings = settings.settings.search()
        if name.isdecimal() and 0 <= int(name) <= len(all_settings):
            name = all_settings[int(name)].name
        if settings[name]:
            settings.put(name, value if value not in ["''", '""'] else None)
            if name == 'askai.sfx.muted':
                from askai.core.speech.effects import set_muted
                from askai.gestures.background import set_sfx_muted
                muted = settings.get_bool(name)
                set_muted(muted)
                set_sfx_muted(muted)
            if announce:
                text_formatter.commander_print(f"Setting `{name}` changed to %GREEN%{value}%NC%")
        else:
            text_formatter.commander_print(f"%RED%Setting: '{name}' was not found!%NC%")

    @staticmethod
    def get(key: str) -> Optional[SettingsEntry]:
        """Retrieve the setting specified by the key.
        :param key: The key of the setting to retrieve.
        :return: The corresponding SettingsEntry if found, otherwise None.
        """
        if ss := settings[key]:
            text_formatter.commander_print(f"%WHITE%Name: %BLUE%{ss.name}\t%WHITE%Value: %GREEN%{ss.value}%NC%")
            return ss
        text_formatter.commander_print(f"%RED%Setting: '{key}' was not found!%NC%")
        return None

    @staticmethod
    def reset() -> None:
        """Reset all settings to their default values."""
        # Command arguments settings must be kept as it was.
        is_interactive: bool = settings.get_bool("askai.interactive.enabled")
        is_speak: bool = settings.get_bool("askai.speak.enabled")
        is_sfx_muted: bool = settings.get_bool("askai.sfx.muted")
        is_debug: bool = settings.get_bool("askai.debug.enabled")
        is_cache: bool = settings.get_bool("askai.cache.enabled")
        settings.defaults()
        configs.clear_devices()
        # Put back the command argument settings.
        settings.put("askai.interactive.enabled", is_interactive)
        settings.put("askai.speak.enabled", is_speak)
        settings.put("askai.sfx.muted", is_sfx_muted)
        settings.put("askai.debug.enabled", is_debug)
        settings.put("askai.cache.enabled", is_cache)
        text_formatter.commander_print(f"%GREEN%Factory settings reset!%NC%")
