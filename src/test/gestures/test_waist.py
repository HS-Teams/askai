import unittest
from types import SimpleNamespace as NS
from askai.gestures.waist import waist_boundary, WaistBoundary


def body():
    pose = [NS(x=.5, y=.5, visibility=.99, presence=.99) for _ in range(33)]
    for index, x, y in ((11, .35, .2), (12, .65, .2), (23, .4, .65), (24, .6, .75), (16, .55, .4)):
        pose[index].x, pose[index].y = x, y
    return NS(pose_landmarks=[pose])


class WaistTests(unittest.TestCase):
    def test_boundary_follows_hips_including_body_movement(self):
        result = body()
        waist = waist_boundary(result, [], 1.)
        self.assertEqual(waist, WaistBoundary((.4, .65), (.6, .75), None))
        for point in result.pose_landmarks[0]:
            point.y -= .1
        moved = waist_boundary(result, [], 1.)
        self.assertAlmostEqual(moved.height_at(.5), waist.height_at(.5) - .1)

    def test_missing_cropped_or_uncertain_body_has_no_boundary(self):
        self.assertIsNone(waist_boundary(NS(pose_landmarks=[]), [], 1.))
        self.assertIsNone(waist_boundary(NS(pose_landmarks=[[]]), [], 1.))
        for index in (11, 12, 23, 24):
            for field, value in (('visibility', .69), ('presence', .69), ('presence', None),
                                 ('x', float('nan')), ('y', 1.01), ('y', -.01)):
                with self.subTest(index=index, field=field, value=value):
                    result = body()
                    setattr(result.pose_landmarks[0][index], field, value)
                    self.assertIsNone(waist_boundary(result, [], 1.))

    def test_collapsed_hips_and_upside_down_body_are_rejected(self):
        result = body()
        result.pose_landmarks[0][23].x = .6
        self.assertIsNone(waist_boundary(result, [], 1.))
        result = body()
        result.pose_landmarks[0][11].y = result.pose_landmarks[0][12].y = .9
        self.assertIsNone(waist_boundary(result, [], 1.))

    def test_hand_must_match_the_detected_body_right_wrist(self):
        self.assertIsNotNone(waist_boundary(body(), [(.55, .4)] * 21, 1.))
        self.assertIsNone(waist_boundary(body(), [(.95, .4)] * 21, 1.))
        result = body()
        result.pose_landmarks[0][16].visibility = .2
        self.assertIsNone(waist_boundary(result, [(.55, .4)] * 21, 1.))

    def test_mirroring_keeps_the_same_physical_side_of_sloped_line(self):
        waist = waist_boundary(body(), [], 1.)
        for x in (.1, .4, .9):
            self.assertAlmostEqual(waist.height_at(x), waist.mirrored().height_at(1-x))
        for x, y, accepted in ((.4, .64, True), (.4, .65, False), (.6, .7, True), (.6, .76, False)):
            points = [(x, y)] * 21
            self.assertEqual(waist.allows(points), accepted)
            self.assertEqual(waist.mirrored().allows([(1-x, y)] * 21), accepted)
        self.assertFalse(waist.allows([]))
        self.assertFalse(waist.allows([(float('nan'), .3)] * 21))

    def test_arm_angle_uses_shoulder_hand_and_torso_with_aspect_correction(self):
        from math import cos, radians, sin
        for aspect in (1., 4 / 3, 16 / 9):
            for angle in (0., 30., 60., 90., 120., 150., 180.):
                with self.subTest(aspect=aspect, angle=angle):
                    result = body()
                    pose = result.pose_landmarks[0]
                    pose[24].x, pose[24].y = .65, .75
                    pose[16].x = .65 + .1 * sin(radians(angle)) / aspect
                    pose[16].y = .2 + .1 * cos(radians(angle))
                    points = [(pose[16].x, pose[16].y)] * 21
                    waist = waist_boundary(result, points, aspect)
                    self.assertAlmostEqual(waist.arm_angle, angle)
                    self.assertAlmostEqual(waist.mirrored().arm_angle, angle)

    def test_tilting_body_preserves_relative_arm_angle(self):
        from math import cos, radians, sin
        result = body()
        pose = result.pose_landmarks[0]
        pose[24].x = pose[12].x
        pose[16].x, pose[16].y = .75, .2
        for point in pose:
            x, y = point.x - .5, point.y - .5
            turn = radians(15)
            point.x = .5 + x * cos(turn) - y * sin(turn)
            point.y = .5 + x * sin(turn) + y * cos(turn)
        waist = waist_boundary(result, [(pose[16].x, pose[16].y)] * 21, 1.)
        self.assertAlmostEqual(waist.arm_angle, 90.)

    def test_missing_hand_or_collapsed_arm_has_no_angle(self):
        self.assertIsNone(waist_boundary(body(), [], 1.).arm_angle)
        result = body()
        pose = result.pose_landmarks[0]
        pose[16].x, pose[16].y = pose[12].x, pose[12].y
        self.assertIsNone(waist_boundary(result, [(pose[16].x, pose[16].y)] * 21, 1.).arm_angle)
