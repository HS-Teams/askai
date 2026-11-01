"""Two-finger scroll recognition and displacement-based wheel steps."""
from math import hypot
from time import monotonic

TOP_LIMIT = .25
BOTTOM_LIMIT = .75
NEUTRAL_TOP = .45
NEUTRAL_BOTTOM = .55
SCROLL_INTERVAL = .1
MAX_STEPS = 8


def is_scroll_hand(points, aspect):
    points = [(x * aspect, y) for x, y in points]
    wrist = points[0]
    def radius(index):
        return hypot(points[index][0] - wrist[0], points[index][1] - wrist[1])
    return (all(radius(tip) > radius(joint) * 1.15 for joint, tip in ((6, 8), (10, 12)))
            and all(radius(tip) < radius(joint) * .95 for joint, tip in ((3, 4), (14, 16), (18, 20))))


class ScrollMotion:
    def __init__(self, clock=monotonic):
        self._clock = clock
        self.reset()

    def reset(self):
        self._last_tick = None
        self._edge = None
        self.boundary = None

    def update(self, y):
        now = self._clock()
        self.boundary = None
        edge = 'top' if y <= TOP_LIMIT else 'bottom' if y >= BOTTOM_LIMIT else None
        if self._last_tick is None:
            self._last_tick = now
            return 0
        if edge:
            if edge != self._edge:
                self.boundary = edge
            self._edge = edge
            self._last_tick = now
            return 0
        self._edge = None
        if NEUTRAL_TOP <= y <= NEUTRAL_BOTTOM:
            self._last_tick = now
            return 0
        if now - self._last_tick < SCROLL_INTERVAL:
            return 0
        self._last_tick = now
        distance = NEUTRAL_TOP - y if y < NEUTRAL_TOP else y - NEUTRAL_BOTTOM
        steps = max(1, min(MAX_STEPS, int(distance / .2 * MAX_STEPS)))
        return steps if y < NEUTRAL_TOP else -steps
