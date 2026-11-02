"""Rock hand: index and little fingers extended, middle and ring folded."""
from math import hypot


def is_rock_hand(points, aspect):
    wrist = points[0]
    def radius(index):
        return hypot((points[index][0] - wrist[0]) * aspect, points[index][1] - wrist[1])
    return (all(radius(tip) > radius(joint) * 1.15 for joint, tip in ((6, 8), (18, 20)))
            and all(radius(tip) < radius(joint) * .95 for joint, tip in ((10, 12), (14, 16))))
