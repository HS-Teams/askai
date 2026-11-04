"""Non-blocking terminal cancellation for PTT and dictation."""
import sys
from contextlib import contextmanager
from contextvars import ContextVar

from hspylib.modules.cli.keyboard import Keyboard


_cancellation_check = ContextVar('speech_cancellation_check', default=None)


@contextmanager
def capture_cancellation(check):
    """Let the active UI own its keyboard while recording on a worker thread."""
    token = _cancellation_check.set(check)
    try:
        yield
    finally:
        _cancellation_check.reset(token)


def cancel_requested():
    check = _cancellation_check.get()
    if check is not None:
        return check()
    return sys.stdin.isatty() and Keyboard.wait_keystroke(
        blocking=False, ignore_error_keys=True,
    ) == Keyboard.VK_ESC
