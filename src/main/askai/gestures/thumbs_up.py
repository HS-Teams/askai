"""Thumb pointing up with the other four fingers folded."""
from math import hypot

STRAIGHT_COSINE = .9
MAX_HORIZONTAL_RATIO = .36
MIN_THUMB_HEIGHT_RATIO = .5
FOLDED_RATIO = .9
FOLDED_FINGERS = ((6, 8), (10, 12), (14, 16), (18, 20))


def is_thumbs_up(points, aspect):
    points = [(x * aspect, y) for x, y in points]
    wrist = points[0]
    for joint, tip in FOLDED_FINGERS:
        if hypot(points[tip][0] - wrist[0], points[tip][1] - wrist[1]) >= FOLDED_RATIO * hypot(
                points[joint][0] - wrist[0], points[joint][1] - wrist[1]):
            return False
    base, joint, tip = points[2], points[3], points[4]
    u = (joint[0] - base[0], joint[1] - base[1])
    v = (tip[0] - joint[0], tip[1] - joint[1])
    lengths = hypot(*u) * hypot(*v)
    palm_width = hypot(points[5][0] - points[17][0], points[5][1] - points[17][1])
    return (lengths > 0 and (u[0] * v[0] + u[1] * v[1]) / lengths >= STRAIGHT_COSINE
            and tip[1] < joint[1] < base[1]
            and abs(tip[0] - base[0]) <= MAX_HORIZONTAL_RATIO * (base[1] - tip[1])
            and palm_width > 0
            and base[1] - tip[1] >= MIN_THUMB_HEIGHT_RATIO * palm_width
            and tip[1] < min(points[i][1] for i in (5, 6, 9, 10, 13, 14, 17, 18)))
