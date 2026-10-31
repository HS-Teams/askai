"""Pace text progress to audio duration through an injected view callback."""
from time import monotonic


def reveal_text(text, duration, cancelled, update):
    started = monotonic()
    length = len(text)
    while not cancelled.is_set():
        fraction = min(1.0, (monotonic() - started) / duration) if duration > 0 else 1.0
        update(text[:int(length * fraction)])
        if fraction >= 1:
            return
        cancelled.wait(.05)

