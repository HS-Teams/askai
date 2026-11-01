"""Phone gesture: thumb and little finger extended, middle three folded."""
from math import hypot


def is_phone_hand(points, aspect):
    points = [(x * aspect, y) for x, y in points]
    wrist = points[0]
    def radius(index):
        return hypot(points[index][0] - wrist[0], points[index][1] - wrist[1])
    return (all(radius(tip) > radius(joint) * 1.15 for joint, tip in ((3, 4), (18, 20)))
            and all(radius(tip) < radius(joint) * .95 for joint, tip in ((6, 8), (10, 12), (14, 16))))
