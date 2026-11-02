"""Render asynchronous replies above the active line editor on its own thread."""
from askai.cli.suggestions import input_suggestion
from queue import Empty, Queue
from threading import RLock, Event
from hspylib.modules.cli.keyboard import Keyboard
import select
import sys
import termios
import tty
from clitt.core.tui.line_input.keyboard_input import KeyboardInput
from clitt.core.term.commons import Direction

_lock = RLock()
_active = None


def present(action):
    with _lock:
        if _active is not None:
            _active.messages.put(action)
            return
    action()


def request_voice():
    with _lock:
        if _active is None or not _active.allow_voice or _active.text:
            return False
        _active.voice_requested.set()
        return True


class PromptInput(KeyboardInput):
    def __init__(self, prompt, placeholder, allow_voice=False):
        super().__init__(prompt, placeholder)
        self.messages = Queue()
        self.allow_voice = allow_voice
        self.voice_requested = Event()

    def _render_suggestions(self):
        candidate = input_suggestion(self.text, self._HISTORY,
                                     case_sensitive=not self._case_insensitive)
        hint = candidate[len(self.text):] if candidate else ''
        self.cursor.erase(Direction.DOWN)
        if hint:
            self.write(f"%GRAY%{hint}%NC%")
            self.cursor.move(len(hint), Direction.LEFT)
        self._suggestion = hint
        return hint

    def handle_keypress(self):
        self.flush_messages()
        if self.voice_requested.is_set():
            self.voice_requested.clear()
            if not self.text:
                self.text = Keyboard.VK_CTRL_L
                self._done = True
                return Keyboard.VK_CTRL_L
        fd = sys.stdin.fileno()
        attributes = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd, termios.TCSANOW)
            ready = bool(select.select([sys.stdin], [], [], .05)[0])
        finally:
            termios.tcsetattr(fd, termios.TCSANOW, attributes)
        if ready:
            return super().handle_keypress()
        return None

    def flush_messages(self):
        while True:
            try:
                action = self.messages.get_nowait()
            except Empty:
                return
            self.cursor.move(self._offset[0], Direction.UP)
            self.cursor.move(self._offset[1], Direction.LEFT)
            self.write('\r')
            self.cursor.erase(Direction.DOWN)
            self._offset = (0, 0)
            try:
                action()
            finally:
                self._offset = (0, 0)
                self.render()


def line_input(prompt, placeholder=None, allow_voice=False):
    global _active
    editor = PromptInput(prompt, placeholder, allow_voice)
    with _lock:
        previous, _active = _active, editor
    try:
        return editor.execute()
    finally:
        with _lock:
            _active = previous
        # Input may have completed just as another reply was queued.
        while not editor.messages.empty():
            editor.messages.get_nowait()()
