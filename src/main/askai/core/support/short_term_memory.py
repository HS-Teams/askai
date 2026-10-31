"""Bounded conversation memory and explicit task state owned by AskAI."""

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    recordable: bool = True


class ShortTermMemory:
    def __init__(self, capacity: int):
        if capacity < 1:
            raise ValueError("Memory capacity must be positive")
        self._messages = deque(maxlen=capacity)
        self.pending: dict[str, str] = {}

    @property
    def messages(self) -> list[Message]:
        return list(self._messages)

    def add(self, role: str, content: str, *, recordable: bool = True) -> None:
        if role not in {"human", "user", "assistant", "system"}:
            raise ValueError(f"Invalid message role: {role}")
        self._messages.append(Message(role, content, recordable))

    def clear(self) -> None:
        self._messages.clear()
        self.pending.clear()
