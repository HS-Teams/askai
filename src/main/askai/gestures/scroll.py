"""Rotation-invariant 3D two-finger recognition and height-based wheel steps."""
from math import dist
from time import monotonic

TOP_LIMIT = .25
BOTTOM_LIMIT = .75
NEUTRAL_TOP = .45
NEUTRAL_BOTTOM = .55
SCROLL_INTERVAL = .1
MAX_STEPS = 8
EXTENDED_JOINT_COSINE = .5  # At most 60 degrees of bend at each finger joint.


def is_scroll_hand(world_points):
    alignments = [_finger_alignment(world_points, base) for base in (5, 9, 13, 17)]
    if any(value is None for value in alignments):
        return False
    return (all(value >= EXTENDED_JOINT_COSINE for value in alignments[:2])
            and all(value < EXTENDED_JOINT_COSINE for value in alignments[2:]))


def _finger_alignment(points, base):
    alignments = []
    for joint in (base + 1, base + 2):
        before, pivot, after = points[joint - 1:joint + 2]
        length = dist(before, pivot) * dist(pivot, after)
        if length == 0:
            return None
        dot = sum((b - a) * (c - b) for a, b, c in zip(before, pivot, after))
        alignments.append(dot / length)
    return min(alignments)


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
