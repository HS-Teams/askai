"""Detect an extended thumb and four extended fingers."""
from math import hypot


def is_open_palm(points, aspect):
    points = [(x * aspect, y) for x, y in points]
    wrist = points[0]
    for base, joint, tip in ((2, 3, 4), (5, 6, 8), (9, 10, 12), (13, 14, 16), (17, 18, 20)):
        a, b, c = points[base], points[joint], points[tip]
        u, v = (b[0]-a[0], b[1]-a[1]), (c[0]-b[0], c[1]-b[1])
        lengths = hypot(*u) * hypot(*v)
        if lengths == 0 or (u[0]*v[0] + u[1]*v[1]) / lengths < .5:
            return False
        if hypot(c[0]-wrist[0], c[1]-wrist[1]) <= hypot(b[0]-wrist[0], b[1]-wrist[1]):
            return False
    return True
