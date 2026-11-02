"""Transient, single-line listening status; never appended to the conversation."""

from rich.status import Status
from rich.text import Text


class ListeningIndicator:
    def __init__(self, console, translate):
        self._status = Status("", console=console, spinner="dots")
        self._translate = translate
        self._active = False

    def update(self, listening: bool, text: str = ""):
        if not listening:
            self._status.stop()
            self._active = False
            return
        # Translate the label, not each changing time value.
        label, separator, timer = text.rpartition(" ")
        rendered = (
            self._translate(label) + separator + timer
            if separator
            else self._translate(text)
        )
        self._status.update(
            Text(rendered, style="green", no_wrap=True, overflow="ellipsis")
        )
        if not self._active:
            self._status.start()
            self._status.update(spinner="dots")
            self._active = True
