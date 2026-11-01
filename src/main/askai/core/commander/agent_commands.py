"""Collect agent-requested commands for execution after the active agent turn."""
from contextlib import contextmanager
from contextvars import ContextVar


_pending_commands = ContextVar('askai_agent_commands', default=None)


@contextmanager
def command_requests():
    pending = []
    token = _pending_commands.set(pending)
    try:
        yield pending
    finally:
        _pending_commands.reset(token)


def queue_command(command, arguments, cancelled):
    pending = _pending_commands.get()
    if pending is None:
        raise ValueError('No active AskAI command session')
    pending.append(([command, *arguments], cancelled))
