"""Enforce a bounded inline turn; continuity belongs to the agent session."""

from contextlib import contextmanager
import os
from askai.core.agents.contracts import AgentError

MAX_INPUT_CHARS = 1_048_576
DEFAULT_CONTEXT_TOKENS = 32768


@contextmanager
def prepared_input(instruction: str):
    import tiktoken

    budget = int(os.getenv("ASKAI_CONTEXT_BUDGET", str(DEFAULT_CONTEXT_TOKENS)))
    if budget < 1024:
        raise AgentError("ASKAI_CONTEXT_BUDGET must be at least 1024 tokens")
    if (
        len(instruction) > MAX_INPUT_CHARS
        or len(
            tiktoken.get_encoding("cl100k_base").encode(
                instruction, disallowed_special=()
            )
        )
        > budget
    ):
        raise AgentError(
            "Current request exceeds the input budget. Send a smaller request; previous context stays in the agent session."
        )
    yield instruction
