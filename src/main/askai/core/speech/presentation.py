"""Pace text progress to audio duration through an injected view callback."""
from time import monotonic
from askai.core.speech.audio_tags import strip_audio_tags


def reveal_text(text, duration, cancelled, update):
    import re
    from askai.core.speech.timing import PlaybackTiming

    timing = duration if isinstance(duration, PlaybackTiming) else None
    seconds = timing.duration if timing else duration
    boundaries = [match.end() for match in re.finditer(r'\S+\s*', text)]
    alignment = timing.alignment if timing else None
    ends = None
    if alignment and ''.join(alignment['characters']) == text:
        ends = alignment['character_end_times_seconds']
        if len(ends) != len(text):
            ends = None
    started = monotonic()
    previous = None
    while not cancelled.is_set():
        elapsed = timing.position if timing else monotonic() - started
        complete = timing.finished.is_set() if timing else elapsed >= seconds
        if complete:
            visible = text
        elif ends:
            boundary = max((end for end in boundaries if ends[end - 1] <= elapsed * timing.tempo), default=0)
            visible = text[:boundary]
        else:
            fraction = min(1.0, elapsed / seconds) if seconds > 0 else 1.0
            boundary = max((end for end in boundaries if end <= len(text) * fraction), default=0)
            visible = text[:boundary]
        if visible != previous:
            update(visible)
            previous = visible
        if complete:
            return
        cancelled.wait(.05)


NARRATION_PREFIX = "降 "


def format_narration(narration):
    """Decorate only the visual narration; synthesis keeps the original text."""
    prefix = NARRATION_PREFIX if narration.spoken else ""
    return narration.before + prefix + strip_audio_tags(narration.spoken) + narration.after
