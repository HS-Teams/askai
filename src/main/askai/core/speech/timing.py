"""Audio-relative character alignment shared by synthesis and presentation."""
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from threading import Event


@dataclass
class PlaybackTiming:
    duration: float
    tempo: float = 1
    position: float = 0
    finished: Event = field(default_factory=Event)
    alignment: dict | None = None


def timing_path(path):
    return Path(str(path) + '.timing.json')


def read_alignment(path):
    try:
        value = json.loads(timing_path(path).read_text())
        chars, ends = value['characters'], value['character_end_times_seconds']
        if (not isinstance(chars, list) or not all(isinstance(c, str) for c in chars)
                or len(chars) != len(ends) or not ends
                or any(type(t) not in (int, float) or not math.isfinite(t) or t < 0 for t in ends)
                or any(a > b for a, b in zip(ends, ends[1:]))):
            return None
        return value
    except (OSError, ValueError, KeyError, TypeError):
        return None
