"""Enforce a bounded inline turn; continuity belongs to the agent session."""

from contextlib import contextmanager
from askai.core.agents.contracts import AgentError

MAX_INPUT_CHARS = 1_048_576


@contextmanager
def prepared_input(instruction: str, context_window: int | None = None):
    import tiktoken

    if (
        len(instruction) > MAX_INPUT_CHARS
        or (context_window is not None and len(
            tiktoken.get_encoding("cl100k_base").encode(
                instruction, disallowed_special=()
            )
        )
        > context_window)
    ):
        raise AgentError(
            "Current request exceeds the input budget. Send a smaller request; previous context stays in the agent session."
        )
    yield instruction
