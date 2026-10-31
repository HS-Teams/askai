#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.support.chat_context
      @file: chat_context.py
   @created: Fri, 28 Feb 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""

from askai.core.component.cache_service import cache
from askai.exception.exceptions import TokenLengthExceeded
from collections import defaultdict, deque, namedtuple
from functools import partial, reduce
from hspylib.core.preconditions import check_argument
from typing import Any, AnyStr, get_args, Literal, Optional, TypeAlias

import os

ChatRoles: TypeAlias = Literal["system", "human", "assistant"]

ContextRaw: TypeAlias = list[dict[str, str]]

ChatEntries: TypeAlias = list[tuple[str, str]]

ContextEntry = namedtuple("ContextEntry", ["role", "content"])


class ChatContext:
    """Provide a chat context helper for AI engines."""


    def __init__(self, token_limit: int, max_context_size: int):
        self._store: dict[AnyStr, deque] = defaultdict(partial(deque, maxlen=max_context_size))
        self._token_limit: int = token_limit * 1024  # The limit is given in KB
        self._max_context_size: int = max_context_size

    def __str__(self):
        ln: str = os.linesep
        return ln.join(f"'{k}': '{v}'" + ln for k, v in self.store.items())

    def __getitem__(self, key) -> deque[ContextEntry]:
        return self.store[key]

    def __iter__(self):
        return zip(self.store.keys().__iter__(), self.store.values().__iter__())

    def __len__(self):
        return self.store.__len__()

    @property
    def keys(self) -> list[AnyStr]:
        return [str(k) for k in self.store.keys()]

    @property
    def store(self) -> dict[Any, deque]:
        return self._store

    @property
    def max_context_size(self) -> int:
        return self._max_context_size

    @property
    def token_limit(self) -> int:
        return self._token_limit

    def push(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Push a context message to the chat with the specified role.
        :param key: The identifier for the context message.
        :param content: The content of the message to push.
        :param role: The role associated with the message (default is "human").
        :return: The updated chat context.
        """
        check_argument(role in get_args(ChatRoles), f"Invalid ChatRole: '{role}'")
        if (token_length := (self.length(key)) + len(content)) > self._token_limit:
            raise TokenLengthExceeded(f"Required token length={token_length}  limit={self._token_limit}")
        if (entry := ContextEntry(role, str(content).strip())) not in (ctx := self.store[key]):
            ctx.append(entry)

        return self.get(key)

    def get(self, key: str) -> ContextRaw:
        """Retrieve a context message identified by the specified key.
        :param key: The identifier for the context message.
        :return: The context message associated with the key.
        """

        return [{"role": ctx.role, "content": ctx.content} for ctx in self.store[key]] or []

    def set(self, key: str, content: Any, role: ChatRoles = "human") -> ContextRaw:
        """Set the context message in the chat with the specified role.
        :param key: The identifier for the context message.
        :param content: The content of the message to set.
        :param role: The role associated with the message (default is "human").
        :return: The updated chat context.
        """
        self.clear(key)
        return self.push(key, content, role)

    def remove(self, key: str, index: int) -> Optional[str]:
        """Remove a context message from the chat at the specified index.
        :param key: The identifier for the context message list.
        :param index: The position of the message to remove within the list.
        :return: The removed message if successful, otherwise None.
        """
        val = None
        if ctx := self.store[key]:
            if index < len(ctx):
                val = ctx[index]
                del ctx[index]
        return val

    def length(self, key: str):
        """Return the length of the context identified by the specified key.
        :param key: The identifier for the context.
        :return: The length of the context (e.g., number of content entries).
        """
        ctx = self.store[key]
        return reduce(lambda total, e: total + len(e.content), ctx, 0) if len(ctx) > 0 else 0

    def join(self, *keys: str) -> ChatEntries:
        """Join multiple contexts identified by the specified keys.
        :param keys: The identifiers for the contexts to join.
        :return: The combined chat context.
        """
        context: ChatEntries = []
        token_length = 0
        for key in keys:
            ctx: ContextRaw = self.get(key)
            content: str = os.linesep.join([tk["content"] for tk in ctx])
            token_length += len(content or "")
            if token_length > self._token_limit:
                raise TokenLengthExceeded(f"Required token length={token_length}k  limit={self._token_limit}k")
            if content and ctx not in context:
                list(map(context.append, [(t["role"], t["content"]) for t in ctx]))
        return context

    def flat(self, *keys: str) -> str:
        """Render selected context for prompts without provider-specific message objects."""
        return "\n".join(f"{role}: {content}" for role, content in self.join(*keys))

    def messages(self, *keys: str) -> list[dict]:
        return [{"role": "user" if role == "human" else role, "content": content}
                for role, content in self.join(*keys)]

    def clear(self, *keys: str) -> int:
        """Clear all chat contexts specified by the provided keys.
        :param keys: The identifiers for the contexts to clear.
        :return: The number of contexts that were cleared.
        """

        count = 0
        contexts = list(keys or self.store.keys())
        while contexts and (key := contexts.pop()):
            if key in self.store:
                del self.store[key]
                count += 1
        return count

    def forget(self, *keys: str) -> None:
        """Forget all entries pushed to the chat context for the specified keys.
        :param keys: The identifiers for the contexts to forget.
        """
        self.clear(*keys)

    def size(self, key: str) -> int:
        """Return the number of entries in the context specified by the given key.
        :param key: The identifier for the context.
        :return: The number of entries in the context.
        """

        return len(self.store[key])

    def save(self) -> None:
        """Save the current context window to the cache."""
        ctx: ChatEntries = self.join(*self.store.keys())
        ctx_str: list[str] = [f"{role}: {msg}" for role, msg in ctx]
        cache.save_context(ctx_str)
