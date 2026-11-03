"""Scroll recognition must survive wrist rotation and projected finger overlap."""
from math import cos, radians, sin
import unittest
from unittest.mock import Mock

import numpy as np

from askai.gestures.controller import GestureController, GestureState
from askai.gestures.scroll import is_scroll_hand
from landmark_fixtures import POINTER_WAIST, world_points
from test_scroll import fingers


def observe(points, pitch, yaw, roll, aspect):
    x, y, z = map(radians, (pitch, yaw, roll))
    rx = np.array(((1, 0, 0), (0, cos(x), -sin(x)), (0, sin(x), cos(x))))
    ry = np.array(((cos(y), 0, sin(y)), (0, 1, 0), (-sin(y), 0, cos(y))))
    rz = np.array(((cos(z), -sin(z), 0), (sin(z), cos(z), 0), (0, 0, 1)))
    spatial = (np.asarray(points) - points[0]) @ (rz @ ry @ rx).T
    image = [(.5 + x * 3 / aspect, .35 + y * 3) for x, y, _ in spatial]
    return image, spatial.tolist()


class ScrollDepthTests(unittest.TestCase):
    def test_scroll_accepts_free_thumb_and_joined_or_separated_fingers(self):
        for thumb in ((.4, .8), (.1, .65), (.05, .2)):
            for tips in (((.40, .2), (.42, .2)), ((.28, .2), (.52, .2))):
                for yaw in (0, 60, 90, 180):
                    with self.subTest(thumb=thumb, tips=tips, yaw=yaw):
                        pose = fingers()
                        pose[4], pose[8], pose[12] = thumb, *tips
                        image, spatial = observe(world_points(pose), 30, yaw, 90, 1.)
                        self.assertTrue(is_scroll_hand(spatial))
                        control = GestureController(Mock(return_value=0.))
                        state = control.update(image, world_points=spatial, waist=POINTER_WAIST)
                        self.assertEqual(state, GestureState(scrolling=True))

    def test_zero_length_finger_bone_cannot_activate_scroll(self):
        for joint in (6, 7, 10, 11, 14, 15, 18, 19):
            spatial = world_points(fingers())
            spatial[joint] = spatial[joint + 1]
            self.assertFalse(is_scroll_hand(spatial))

    def test_thumb_touching_index_does_not_activate_scroll(self):
        pose = fingers()
        pose[4] = pose[8]
        image, spatial = observe(world_points(pose), 60, 45, 90, 1.)
        control = GestureController(Mock(return_value=0.))
        state = control.update(image, world_points=spatial, waist=POINTER_WAIST)
        self.assertFalse(state.scrolling)

    def test_fingers_bent_towards_camera_are_folded_even_far_from_wrist(self):
        spatial = world_points(fingers())
        for base in (13, 17):
            x = spatial[base][0]
            spatial[base:base + 4] = [(x, .065, 0.), (x, .05, 0.),
                                      (x, .05, .02), (x, .05, .04)]
        for pitch, yaw, roll in ((0, 0, 0), (90, 0, 45), (45, 90, 180), (-60, -75, 90)):
            image, rotated = observe(spatial, pitch, yaw, roll, 1.)
            self.assertTrue(is_scroll_hand(rotated))
            control = GestureController(Mock(return_value=0.))
            state = control.update(image, world_points=rotated, waist=POINTER_WAIST)
            self.assertEqual(state, GestureState(scrolling=True))

    def test_sideways_scroll_stays_active_past_inactivity_timeout(self):
        from askai.gestures.session import run_session
        from landmark_fixtures import WAIST
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        clock = Mock(return_value=0.)
        image, spatial = observe(world_points(fingers()), 0, 90, 0, 1.)
        times = iter((0., .2, 2.5, 3., 5., 10.))

        def capture():
            clock.return_value = next(times)
            return True, np.zeros((100, 100, 3))

        camera.read.side_effect = capture
        tracker.detect.return_value = image, spatial, WAIST
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        run_session(camera, tracker, pointer, view, policy, notify,
                    clock=clock, should_stop=Mock(side_effect=[False] * 6 + [True]))
        self.assertTrue(all(c.args[2].scrolling for c in view.update.call_args_list))
        self.assertNotIn('inactive', [c.args[0] for c in notify.call_args_list])
        self.assertGreater(pointer.scroll.call_count, 1)
        pointer.move.assert_not_called()

    def test_scroll_continues_through_rotations_in_all_three_axes(self):
        for aspect in (1., 4 / 3, 16 / 9):
            clock = Mock(return_value=0.)
            control = GestureController(clock)
            for pitch in (-90, -60, 0, 60, 90):
                for yaw in (-90, -60, 0, 60, 90):
                    for roll in (0, 90, 180, 270):
                        with self.subTest(aspect=aspect, pitch=pitch, yaw=yaw, roll=roll):
                            image, spatial = observe(world_points(fingers()), pitch, yaw, roll, aspect)
                            self.assertTrue(is_scroll_hand(spatial))
                            for _ in range(3):
                                clock.return_value += .2
                                state = control.update(image, aspect, world_points=spatial, waist=POINTER_WAIST)
                                self.assertTrue(state.scrolling)
                                self.assertIsNone(state.pointer)
                                self.assertFalse(state.dragging)
                                self.assertFalse(state.exit_requested)
                                self.assertFalse(state.abort_requested)
                            self.assertGreater(state.scroll_steps, 0)

    def test_edge_on_hand_can_enter_scroll_with_collapsed_image_palm_width(self):
        image, spatial = observe(world_points(fingers()), 0, 90, 0, 1.)
        self.assertAlmostEqual(image[5][0], image[17][0])
        self.assertAlmostEqual(image[5][1], image[17][1])
        control = GestureController(Mock(return_value=0.))
        state = control.update(image, world_points=spatial, waist=POINTER_WAIST)
        self.assertEqual(state, GestureState(scrolling=True))

    def test_projected_two_fingers_do_not_scroll_if_other_fingers_extend_in_depth(self):
        image = fingers()
        for tip in (16, 20):
            with self.subTest(tip=tip):
                spatial = world_points(image)
                x, y, _ = spatial[tip - 3]
                spatial[tip - 2:tip + 1] = [(x, y, depth) for depth in (.015, .03, .05)]
                self.assertFalse(is_scroll_hand(spatial))
                control = GestureController(Mock(return_value=0.))
                state = control.update(image, world_points=spatial, waist=POINTER_WAIST)
                self.assertFalse(state.scrolling)
                self.assertEqual(state.scroll_steps, 0)

    def test_invalid_depth_stops_wheel_and_expires_mode_after_half_second(self):
        image = fingers()
        for invalid in ([], [(0., 0.)] * 21, [(float('nan'), 0., 0.)] * 21, [(0., 0., 0.)] * 21):
            clock = Mock(return_value=0.)
            control = GestureController(clock)
            control.update(image, world_points=world_points(image), waist=POINTER_WAIST)
            for time, active in ((1., True), (1.499, True), (1.5, False)):
                clock.return_value = time
                state = control.update(image, world_points=invalid, waist=POINTER_WAIST)
                self.assertEqual(state, GestureState(scrolling=active))
