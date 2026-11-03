"""Pair planar gesture fixtures with world landmarks and a visible body."""
from askai.gestures.waist import WaistBoundary

WAIST = WaistBoundary((.3, .98), (.7, .98))


def world_points(points, aspect=1.0):
    return [(x * aspect * .1, y * .1, 0.) for x, y in points]


def detection(points, aspect=1.0):
    return points, world_points(points, aspect), WAIST
