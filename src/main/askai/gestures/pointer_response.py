"""Adapt tracking responsiveness without changing the pointer's absolute target."""
from math import exp, hypot
from time import monotonic


class PointerResponse:
    RESPONSE_SECONDS = .15
    FAST_SPEED = 1.5
    MIN_FACTOR = .5
    MAX_FACTOR = 1.5
    MAX_GAP_SECONDS = .25
    MIN_SAMPLE_SECONDS = 1. / 240.

    def __init__(self, baseline, dead_zone, clock=monotonic):
        self._baseline = baseline
        self._dead_zone = dead_zone
        self._clock = clock
        self._previous = None
        self._timestamp = None
        self._value = baseline

    def sample(self, hand, frozen=False):
        now = self._clock()
        previous, timestamp = self._previous, self._timestamp
        self._previous, self._timestamp = hand, now
        if frozen or previous is None or not 0 < now - timestamp <= self.MAX_GAP_SECONDS:
            self._value = self._baseline
            return self._value
        elapsed = now - timestamp
        if elapsed < self.MIN_SAMPLE_SECONDS:
            return self._value
        distance = hypot(*(b - a for a, b in zip(previous, hand)))
        speed = distance / elapsed if distance > self._dead_zone else 0.
        fraction = min(1., speed / self.FAST_SPEED)
        desired = self._baseline * (self.MIN_FACTOR + (self.MAX_FACTOR - self.MIN_FACTOR) * fraction)
        self._value += (1. - exp(-elapsed / self.RESPONSE_SECONDS)) * (desired - self._value)
        return self._value
