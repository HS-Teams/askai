#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.component
      @file: cache_service.py
   @created: Tue, 16 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.core.askai_configs import configs
from askai.core.askai_settings import ASKAI_DIR, CONVERSATION_STARTERS
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from collections import namedtuple
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.tools.commons import file_is_not_empty, touch_file
from hspylib.core.tools.text_tools import hash_text
from hspylib.modules.cache.ttl_cache import TTLCache
from askai.core.support.short_term_memory import Message
from pathlib import Path
from shutil import copyfile
from typing import Optional

import os
import re

# AskAI cache root directory.
CACHE_DIR: Path = Path(f"{ASKAI_DIR}/cache")

# Settings directory.
SETTINGS_DIR: Path = Path(str(ASKAI_DIR) + "/settings")
if not SETTINGS_DIR.exists():
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
AUDIO_DIR: Path = Path(str(CACHE_DIR) + "/audio")
if not AUDIO_DIR.exists():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Camera photo shots cache directory.
PICTURE_DIR: Path = Path(str(CACHE_DIR) + "/pictures")
if not PICTURE_DIR.exists():
    PICTURE_DIR.mkdir(parents=True, exist_ok=True)

# Desktop screenshots cache directory.
SCREENSHOTS_DIR: Path = Path(str(CACHE_DIR) + "/screenshots")
if not SCREENSHOTS_DIR.exists():
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Camera photo shots cache directory.
PHOTO_DIR: Path = Path(str(PICTURE_DIR) + "/photos")
if not PHOTO_DIR.exists():
    PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# Detected faces cache directory.
FACE_DIR: Path = Path(str(PICTURE_DIR) + "/faces")
if not FACE_DIR.exists():
    FACE_DIR.mkdir(parents=True, exist_ok=True)

# Imported image files cache directory.
IMG_IMPORTS_DIR: Path = Path(str(PICTURE_DIR) + "/imports")
if not IMG_IMPORTS_DIR.exists():
    IMG_IMPORTS_DIR.mkdir(parents=True, exist_ok=True)

# AI Generation cache directory.
GEN_AI_DIR: Path = Path(str(CACHE_DIR) + "/generated")
if not GEN_AI_DIR.exists():
    GEN_AI_DIR.mkdir(parents=True, exist_ok=True)

# Voice recordings cache directory.
REC_DIR: Path = Path(str(CACHE_DIR) + "/recordings")
if not REC_DIR.exists():
    REC_DIR.mkdir(parents=True, exist_ok=True)

# Transcribed audio cache directory.
PERSIST_DIR: Path = Path(str(CACHE_DIR) + "/chroma")
if not PERSIST_DIR.exists():
    PERSIST_DIR.mkdir(parents=True, exist_ok=True)

ASKAI_INPUT_HISTORY_FILE: Path = Path(CACHE_DIR / "askai-input-history.txt")
if not file_is_not_empty(str(ASKAI_INPUT_HISTORY_FILE)):
    copyfile(str(CONVERSATION_STARTERS), str(ASKAI_INPUT_HISTORY_FILE))

ASKAI_CONTEXT_FILE: Path = Path(CACHE_DIR / "askai-context-history.txt")
if not file_is_not_empty(str(ASKAI_CONTEXT_FILE)):
    touch_file(str(ASKAI_CONTEXT_FILE))

ASKAI_MEMORY_FILE: Path = Path(CACHE_DIR / "askai-memory-history.txt")
if not file_is_not_empty(str(ASKAI_MEMORY_FILE)):
    touch_file(str(ASKAI_MEMORY_FILE))

GEO_LOC_CACHE_FILE: Path = Path(CACHE_DIR / "geo-location.json")


CacheEntry = namedtuple("CacheEntry", ["key", "expires"])


class CacheService(metaclass=Singleton):
    """Provide a cache service for previously used queries, audio generation, and other recurring operations. This
    class is designed to store and retrieve cached data efficiently, reducing the need for repeated processing and
    enhancing performance.
    """

    INSTANCE: "CacheService"

    ASKAI_CACHE_KEYS: str = "askai-cache-keys"

    ASKAI_CONTEXT_KEY: str = "askai-context-key"

    _TTL_CACHE: TTLCache[str] = TTLCache(ttl_minutes=configs.ttl)

    @staticmethod
    def audio_file_path(text: str, voice: str = "onyx", audio_format: str = "mp3") -> tuple[str, bool]:
        """Retrieve the hashed audio file path and determine whether the file already exists.
        :param text: The text that the audio represents.
        :param voice: The AI voice used for speech synthesis (default is "onyx").
        :param audio_format: The audio file format (default is "mp3").
        :return: A tuple containing the hashed file path as a string and a boolean indicating if the file exists.
        """
        if not configs.is_cache:
            from askai.core.support.cache_policy import transient_audio_path
            return transient_audio_path(audio_format)
        key = f"{text.strip().lower()}-{hash_text(voice)}"
        audio_file_path = f"{str(AUDIO_DIR)}/askai-{hash_text(key)}.{audio_format}"
        return audio_file_path, file_is_not_empty(audio_file_path)

    def __init__(self):
        self._private_inputs = set()
        keys: str | None = self._TTL_CACHE.read(self.ASKAI_CACHE_KEYS) if configs.is_cache else None
        self._cache_keys: set[str] = set(map(str.strip, keys.split(",") if keys else {}))

    @property
    def keys(self) -> set[str]:
        return self._cache_keys

    def save_reply(self, text: str, reply: str) -> Optional[str]:
        """Save an AI reply into the TTL (Time-To-Live) cache.
        :param text: The text to be cached.
        :param reply: The AI reply associated with this text.
        :return: The key under which the reply is saved, or None if the save operation fails.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.save(key, reply)
            self.keys.add(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ",".join(self._cache_keys))
            return key
        return None

    def read_reply(self, text: str) -> Optional[str]:
        """Retrieve AI replies from the TTL (Time-To-Live) cache.
        :param text: The text key to look up in the cache.
        :return: The cached reply associated with the text, or None if not found.
        """
        if configs.is_cache:
            key = text.strip().lower()
            return self._TTL_CACHE.read(key)
        return None

    def del_reply(self, text: str) -> Optional[str]:
        """Delete an AI reply from the TTL (Time-To-Live) cache.
        :param text: The text key whose associated reply is to be deleted from the cache.
        :return: The deleted reply if it existed, or None if no reply was found.
        """
        if configs.is_cache:
            key = text.strip().lower()
            self._TTL_CACHE.delete(key)
            self.keys.remove(key)
            self._TTL_CACHE.save(self.ASKAI_CACHE_KEYS, ",".join(self._cache_keys))
            return text
        return None

    def clear_replies(self) -> list[str]:
        """Clear all cached replies.
        :return: A list of keys for the replies that were deleted from the cache.
        """
        return list(map(self.del_reply, sorted(self.keys)))

    def read_input_history(self) -> list[str]:
        """Retrieve line input queries from the history file.
        :return: A list of input queries stored in the cache.
        """
        if not configs.is_keep_context:
            return []
        history: str = ASKAI_INPUT_HISTORY_FILE.read_text()
        inputs = list(filter(str.__len__, map(str.strip, history.split(os.linesep))))

        return inputs

    def save_input_history(self, history: list[str] = None) -> None:
        """Save input queries into the history file.
        :param history: A list of input queries to be saved. If None, the current input history will be saved.
        """
        inputs = history if history is not None else KeyboardInput.history()
        if not configs.is_keep_context:
            self._private_inputs.update(inputs)
            return
        history = list(dict.fromkeys(self.read_input_history() + [item for item in inputs if item not in self._private_inputs]))
        if history:
            with open(str(ASKAI_INPUT_HISTORY_FILE), "w", encoding=Charset.UTF_8.val) as f_hist:
                list(
                    map(
                        lambda h: f_hist.write(h + "\n"),
                        filter(lambda h: not h.startswith("/"), history),
                    )
                )

    def load_input_history(self, predefined: list[str] = None) -> list[str]:
        """Load input queries from the history file, extending it with a predefined input history.
        :param predefined: A list of predefined input queries to be appended to the final list.
        :return: A list of input queries loaded from the cache.
        """
        history = list()
        if predefined:
            history.extend(list(filter(lambda c: c not in history, predefined)))
        history.extend(self.read_input_history())
        return history

    def save_context(self, context: list[str] = None) -> None:
        """Save the context window entries into the context file.
        :param context: A list of context entries to be saved.
        """
        if not configs.is_keep_context:
            return None
        if context := (context or list()):
            with open(str(ASKAI_CONTEXT_FILE), "w", encoding=Charset.UTF_8.val) as f_hist:
                list(map(lambda h: f_hist.write(h + "\n"), context))

    def read_context(self) -> list[str]:
        """Read the context window entries from the context file.
        :return: A list of context entries retrieved from the cache."""
        if not configs.is_keep_context:
            return []
        flags: int = re.MULTILINE | re.DOTALL | re.IGNORECASE
        context: str = ASKAI_CONTEXT_FILE.read_text()
        return list(filter(str.__len__, map(str.strip, re.split(r"(human|assistant|system):", context, flags=flags))))

    def save_memory(self, memory: list[Message] = None) -> None:
        """Save the context window entries into the context file.
        :param memory: A list of memory entries to be saved.
        """
        if not configs.is_keep_context:
            return None

        def _get_role_(msg: Message) -> str:
            return "human" if msg.role == "user" else msg.role

        if memory := [message for message in (memory or []) if message.recordable]:
            with open(str(ASKAI_MEMORY_FILE), "w", encoding=Charset.UTF_8.val) as f_hist:
                list(map(lambda m: f_hist.write(f"{_get_role_(m)}: {m.content}\n"), memory))

    def read_memory(self) -> list[str]:
        """Reads and parses the memory from the context file.
        :return: A list of non-empty, stripped strings split by roles (human, assistant, system).
        """
        if not configs.is_keep_context:
            return []
        flags: int = re.MULTILINE | re.DOTALL | re.IGNORECASE
        memory: str = ASKAI_MEMORY_FILE.read_text()
        return list(filter(str.__len__, map(str.strip, re.split(r"(human|assistant|system):", memory, flags=flags))))


assert (cache := CacheService().INSTANCE) is not None
