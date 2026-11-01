"""Explicit selection of specialized runtimes; never substitute another provider."""

from askai.core.agents.codex import CodexBackend
from askai.core.agents.contracts import AgentError

AGENT_NAMES = ("codex", "claude", "cursor")


def normalize_agent(name: str) -> str:
    name = name.strip().casefold()
    if name not in AGENT_NAMES:
        raise AgentError(f"Unknown agent '{name}'. Choose Codex, Claude or Cursor.")
    return name


def create_backend(name: str, *, debug=lambda: False):
    name = normalize_agent(name)
    if name == "codex":
        return CodexBackend(debug=debug)
    raise AgentError(
        f"The {name.title()} adapter is not implemented yet. No other agent was started."
    )
