"""Non-blocking terminal input for finishing dictation."""
import sys

from hspylib.modules.cli.keyboard import Keyboard


def finish_requested():
    return sys.stdin.isatty() and Keyboard.wait_keystroke(
        blocking=False, ignore_error_keys=True,
    ) == Keyboard.VK_ESC
