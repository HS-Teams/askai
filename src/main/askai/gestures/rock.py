"""Recognize Heavy Metal from 3D finger distances, independent of wrist rotation."""
from math import dist

EXTENDED_RATIO = 1.15
FOLDED_RATIO = .95


def is_rock_hand(world_points):
    wrist = world_points[0]
    def radius(index):
        return dist(world_points[index], wrist)
    return (all(radius(tip) > radius(joint) * EXTENDED_RATIO for joint, tip in ((6, 8), (18, 20)))
            and all(radius(tip) < radius(joint) * FOLDED_RATIO for joint, tip in ((10, 12), (14, 16))))
