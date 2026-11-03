"""Use visible hip landmarks as the body-relative waist boundary."""
from dataclasses import dataclass
from math import hypot, isfinite

MIN_CONFIDENCE = .7
MIN_HIP_WIDTH = .01
WRIST_MATCH_RATIO = .5
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12
RIGHT_WRIST = 16
LEFT_HIP, RIGHT_HIP = 23, 24


@dataclass(frozen=True)
class WaistBoundary:
    left: tuple[float, float]
    right: tuple[float, float]

    def height_at(self, x):
        fraction = (x - self.left[0]) / (self.right[0] - self.left[0])
        return self.left[1] + fraction * (self.right[1] - self.left[1])

    def allows(self, points):
        return len(points) == 21 and all(
            isfinite(points[i][0]) and isfinite(points[i][1])
            and points[i][1] < self.height_at(points[i][0]) for i in (4, 8))

    def mirrored(self):
        return WaistBoundary((1 - self.right[0], self.right[1]), (1 - self.left[0], self.left[1]))


def _visible(point):
    return (all(value is not None and isfinite(value) for value in
                (point.x, point.y, point.visibility, point.presence))
            and 0 <= point.x <= 1 and 0 <= point.y <= 1
            and point.visibility >= MIN_CONFIDENCE and point.presence >= MIN_CONFIDENCE)


def waist_boundary(result, hand_points, aspect):
    if len(result.pose_landmarks) != 1 or len(result.pose_landmarks[0]) != 33:
        return None
    pose = result.pose_landmarks[0]
    if not all(_visible(pose[i]) for i in (LEFT_SHOULDER, RIGHT_SHOULDER, LEFT_HIP, RIGHT_HIP)):
        return None
    hips = sorted(((pose[i].x, pose[i].y) for i in (LEFT_HIP, RIGHT_HIP)))
    if (hips[1][0] - hips[0][0]) * aspect < MIN_HIP_WIDTH:
        return None
    shoulder = tuple(sum(getattr(pose[i], axis) for i in (LEFT_SHOULDER, RIGHT_SHOULDER)) / 2
                     for axis in ('x', 'y'))
    hip = tuple((hips[0][axis] + hips[1][axis]) / 2 for axis in (0, 1))
    if shoulder[1] >= hip[1]:
        return None
    if hand_points:
        wrist = pose[RIGHT_WRIST]
        torso = hypot((shoulder[0] - hip[0]) * aspect, shoulder[1] - hip[1])
        if (not _visible(wrist) or hypot((wrist.x - hand_points[0][0]) * aspect,
                                        wrist.y - hand_points[0][1]) > torso * WRIST_MATCH_RATIO):
            return None
    return WaistBoundary(*hips)
