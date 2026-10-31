"""Task delegation and interaction contracts owned by AskAI."""

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable, Protocol


class AgentError(RuntimeError):
    """A runtime, protocol or delegated execution failure."""


@dataclass(frozen=True)
class AgentTask:
    instruction: str
    cwd: Path
    context: str = ""
    session_id: str | None = None
    model: str | None = None
    output_schema: dict | None = None
    read_only: bool = False
    session_name: str | None = None
    persist_history: bool = True


@dataclass(frozen=True)
class AgentEvent:
    kind: str
    session_id: str
    turn_id: str | None = None
    data: dict = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResult:
    session_id: str
    turn_id: str
    answer: str
    status: str
    evidence: tuple[dict, ...] = ()


class AgentBackend(Protocol):
    def run(
        self,
        task: AgentTask,
        emit: Callable[[AgentEvent], None],
        interact: Callable[[str, dict], dict],
        cancelled: Event,
    ) -> AgentResult: ...
