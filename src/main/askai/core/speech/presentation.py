"""Pace text progress to audio duration through an injected view callback."""
from time import monotonic
from askai.core.speech.audio_tags import strip_audio_tags


def reveal_text(text, duration, cancelled, update):
    started = monotonic()
    length = len(text)
    while not cancelled.is_set():
        fraction = min(1.0, (monotonic() - started) / duration) if duration > 0 else 1.0
        update(text[:int(length * fraction)])
        if fraction >= 1:
            return
        cancelled.wait(.05)



NARRATION_PREFIX = "降 "


def format_narration(narration):
    """Decorate only the visual narration; synthesis keeps the original text."""
    prefix = NARRATION_PREFIX if narration.spoken else ""
    return narration.before + prefix + strip_audio_tags(narration.spoken) + narration.after
