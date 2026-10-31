#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support
      @file: askai_settings.py
   @created: Tue, 23 Apr 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.__classpath__ import classpath
from contextlib import redirect_stdout
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import console_out, to_bool
from io import StringIO
from pathlib import Path
from rich import box
from rich.table import Table
from setman.settings.settings import Settings
from setman.settings.settings_config import SettingsConfig
from setman.settings.settings_entry import SettingsEntry
from typing import Any, Optional

import logging as log
import os
import re

# AskAI config directory.
ASKAI_DIR: Path = Path(f'{os.getenv("ASKAI_DIR", os.getenv("HHS_DIR", str(Path.home())))}/askai')
if not ASKAI_DIR.exists():
    ASKAI_DIR.mkdir(parents=True, exist_ok=True)

# Make sure the AskAI directory is exported.
os.environ["ASKAI_DIR"] = str(ASKAI_DIR)

# AskAi conversation starters
CONVERSATION_STARTERS: Path = Path(classpath.resource_path / "conversation-starters.txt")


class AskAiSettings(metaclass=Singleton):
    """The AskAI 'SetMan' Settings."""

    INSTANCE: "AskAiSettings"

    # Current settings version. Updating this value will trigger a database recreation using the defaults.
    __ACTUAL_VERSION: str = "0.4.3"

    __RESOURCE_DIR = str(classpath.resource_path)

    def __init__(self) -> None:
        self._configs = SettingsConfig(self.__RESOURCE_DIR, "application.properties")
        self._settings = Settings(self._configs)
        if not self._settings.count() or self.get("askai.settings.version.id") != self.__ACTUAL_VERSION:
            self.defaults()
        if self.get("askai.session.compact.on.exit", None) is None:
            self.put("askai.session.compact.on.exit", True)

    def __str__(self) -> str:
        return self.search()

    def __repr__(self) -> str:
        return self.__str__()

    def __getitem__(self, name: str) -> Optional[SettingsEntry]:
        return self._settings.get(name)

    def __setitem__(self, name: str, item: Any) -> None:
        self._settings.put(name, name[: name.find(".")], item)

    @property
    def settings(self) -> Settings:
        return self._settings

    def search(self, filters: str | None = None) -> Optional[str]:
        """Search settings using the specified filters.
        :param filters: Optional filters to apply to the search.
        :return: The search results as a string, or None if no results are found.
        """
        data = [(s.name, s.value) for s in self._settings.search(filters)]
        if data:
            table = Table(title="AskAI - Settings", box=box.SQUARE_DOUBLE_HEAD)
            table.add_column("No.", style="white", no_wrap=True)
            table.add_column("Name", style="cyan", no_wrap=True)
            table.add_column("Value", style="green", no_wrap=True)
            for i, d in enumerate(data):
                table.add_row(str(i), d[0], d[1])
            with StringIO() as buf, redirect_stdout(buf):
                console_out.print(table)
                return buf.getvalue()
        return None

    def defaults(self) -> None:
        """Create the default settings database."""
        # AskAI General
        self._settings.clear("askai.*")
        self._settings.put("askai.settings.version.id", "askai", self.__ACTUAL_VERSION)
        self._settings.put("askai.debug.enabled", "askai", False)
        self._settings.put("askai.speak.enabled", "askai", False)
        self._settings.put("askai.cache.enabled", "askai", False)
        self._settings.put("askai.cache.ttl.minutes", "askai", 25)
        self._settings.put("askai.context.keep.conversation", "askai", False)
        self._settings.put("askai.session.compact.on.exit", "askai", True)
        self._settings.put("askai.preferred.language", "askai", "")
        self._settings.put("askai.router.mode.default", "askai", "taius")
        self._settings.put("askai.router.pass.threshold", "askai", "moderate")
        self._settings.put("askai.router.assistive.enabled", "askai", False)
        self._settings.put("askai.default.engine", "askai", "codex")
        self._settings.put("askai.agent.default", "askai", "codex")
        self._settings.put("askai.codex.default.model", "askai", "gpt-6.1-sol")
        self._settings.put("askai.openai.default.model", "askai", "gpt-4o-mini")
        self._settings.put("askai.verbosity.level", "askai", 3)
        self._settings.put("askai.text.to.speech.tempo", "askai", 1)
        self._settings.put("askai.text.splitter.chunk.size", "askai", 1000)
        self._settings.put("askai.text.splitter.chunk.overlap", "askai", 100)
        self._settings.put("askai.rag.retrival.amount", "askai", 3)
        self._settings.put("askai.rag.enabled", "askai", True)
        self._settings.put("askai.ip-api.geo-location.enabled", "askai", True)
        # Router
        self._settings.put("askai.max.short.memory.size", "askai", 15)
        self._settings.put("askai.max.router.iteractions", "askai", 30)
        self._settings.put("askai.max.router.retries", "askai", 3)
        self._settings.put("askai.max.agent.retries", "askai", 5)
        self._settings.put("askai.max.agent.execution.time.seconds", "askai", 45)
        # Recorder
        self._settings.put("askai.recorder.devices", "askai", "")
        self._settings.put("askai.recorder.silence.timeout.millis", "askai", 1700)
        self._settings.put("askai.recorder.end.silence.millis", "askai", 2000)
        self._settings.put("askai.recorder.phrase.limit.millis", "askai", 10000)
        self._settings.put("askai.recorder.tail.margin.millis", "askai", 1500)
        self._settings.put("askai.recorder.noise.detection.duration.millis", "askai", 600)
        self._settings.put("askai.recorder.input.device.auto.swap", "askai", True)
        # Camera
        self._settings.put("askai.camera.face-detect.alg", "askai", "haarcascade_frontalface_default.xml")
        self._settings.put("askai.camera.scale.factor", "askai", 1.1)
        self._settings.put("askai.camera.min.neighbors", "askai", 3)
        self._settings.put("askai.camera.min-max.size", "askai", "100, 100")
        self._settings.put("askai.camera.identity.max.distance", "askai", 0.70)
        # OpenAI
        self._settings.put("askai.openai.speech.to.text.model", "askai", "whisper-1")
        self._settings.put("askai.openai.text.to.speech.model", "askai", "tts-1")
        self._settings.put("askai.openai.text.to.speech.voice", "askai", "onyx")
        self._settings.put("askai.openai.text.to.speech.audio.format", "askai", "mp3")
        log.debug(f"Settings database created !")

    def get(self, key: str, default_value: str | None = "") -> str:
        """Retrieve the setting specified by the given key.
        :param key: The name of the setting to retrieve.
        :param default_value: The value to return if the setting does not exist.
        :return: The setting value if it exists, otherwise the default_value.
        """
        val = self.__getitem__(key)
        return str(val.value) if val else default_value

    def put(self, key: str, value: Any) -> None:
        """Set the setting specified by the given key.
        :param key: The name of the setting to update.
        :param value: The value to associate with the key.
        """
        self.__setitem__(key, value)

    def get_bool(self, key: str, default_value: bool | None = False) -> bool:
        """Retrieve the setting specified by the given key, converting it to boolean.
        :param key: The name of the setting to retrieve.
        :param default_value: The value to return if the setting does not exist.
        :return: The setting value if it exists, otherwise the default_value.
        """
        return to_bool(self.get(key) or default_value)

    def get_int(self, key: str, default_value: int | None = 0) -> int:
        """Retrieve the setting specified by the given key, converting it to integer.
        :param key: The name of the setting to retrieve.
        :param default_value: The value to return if the setting does not exist.
        :return: The setting value if it exists, otherwise the default_value.
        """
        try:
            return int(self.get(key) or default_value)
        except ValueError:
            return default_value

    def get_float(self, key: str, default_value: float | None = 0.0) -> float:
        """Retrieve the setting specified by the given key, converting it to float.
        :param key: The name of the setting to retrieve.
        :param default_value: The value to return if the setting does not exist.
        :return: The setting value if it exists, otherwise the default_value.
        """
        try:
            return float(self.get(key) or default_value)
        except ValueError:
            return default_value

    def get_list(self, key: str, default_value: list | None = None) -> list:
        """Retrieve the setting specified by the given key, converting it to list.
        :param key: The name of the setting to retrieve.
        :param default_value: The value to return if the setting does not exist.
        :return: The setting value if it exists, otherwise the default_value.
        """
        try:
            val: list | None = None
            if str_val := (self.get(key) or ""):
                val = re.split(r"[;,|]", str_val)
            return val or default_value or list()
        except ValueError:
            return default_value or list()


assert (settings := AskAiSettings().INSTANCE) is not None
