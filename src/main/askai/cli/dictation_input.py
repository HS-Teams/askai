"""Non-blocking terminal cancellation for PTT and dictation."""
import sys

from hspylib.modules.cli.keyboard import Keyboard


def cancel_requested():
    return sys.stdin.isatty() and Keyboard.wait_keystroke(
        blocking=False, ignore_error_keys=True,
    ) == Keyboard.VK_ESC
