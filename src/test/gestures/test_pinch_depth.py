from landmark_fixtures import WAIST
"""Wrist rotation must not turn projected fingertip overlap into a mouse press."""
from math import cos, dist, radians, sin
import unittest
from unittest.mock import Mock
import numpy as np
from askai.gestures.controller import GestureController
from askai.gestures.session import run_session


def pointing_hand(pinched=False):
    points = [(0., .03, 0.)] * 21
    points[1:5] = [(-.02, .02, 0.), (-.045, .01, 0.), (-.04, -.02, .01), (-.03, -.04, .01)]
    points[5:9] = [(-.03, 0., 0.), (-.03, -.035, 0.), (-.03, -.06, 0.), (-.03, -.08, 0.)]
    for base, x in ((9, -.01), (13, .01), (17, .03)):
        points[base:base + 4] = [(x, 0., 0.), (x, -.015, 0.), (x, .005, -.01), (x, .01, -.01)]
    if pinched:
        points[4] = (-.025, -.078, .003)
    return points


def observe(points, tilt=0., roll=0., aspect=1., offset=(0., 0.)):
    tilt, roll = radians(tilt), radians(roll)
    tilted = [(x, y * cos(tilt) - z * sin(tilt), y * sin(tilt) + z * cos(tilt))
              for x, y, z in points]
    world = [(x * cos(roll) - y * sin(roll), x * sin(roll) + y * cos(roll), z)
             for x, y, z in tilted]
    image = [(.5 + x * 3 / aspect + offset[0], .5 + y * 3 + offset[1]) for x, y, _ in world]
    return image, world


class PinchDepthTests(unittest.TestCase):
    def test_pointing_and_twisting_with_projected_overlap_never_presses(self):
        for aspect in (1., 4 / 3, 16 / 9):
            for roll in (0., 90., 180., 270.):
                with self.subTest(aspect=aspect, roll=roll):
                    control = GestureController(Mock(return_value=0.))
                    for tilt in (0., 30., 60., 75., 85., 75., 60., 0., -60., -85.):
                        image, world = observe(pointing_hand(), tilt, roll, aspect)
                        if tilt == 75.:
                            projected = [(x * aspect, y) for x, y in image]
                            self.assertLess(dist(projected[4], projected[8]) / dist(projected[5], projected[17]),
                                            control.CLOSE_RATIO)
                        state = control.update(image, aspect, world_points=world)
                        self.assertFalse(state.dragging)
                        self.assertFalse(state.pinched)

    def test_real_pinch_can_start_and_remain_held_in_rotated_or_lowered_pose(self):
        for tilt in (0., 60., 75., 85., -75.):
            for roll in (0., 90., 180.):
                with self.subTest(tilt=tilt, roll=roll):
                    control = GestureController(Mock(return_value=0.))
                    image, world = observe(pointing_hand(), tilt, roll)
                    control.update(image, world_points=world)
                    image, world = observe(pointing_hand(True), tilt, roll)
                    self.assertTrue(control.update(image, world_points=world).dragging)
                    image, world = observe(pointing_hand(True), tilt + 5, roll + 15, offset=(.04, .03))
                    self.assertTrue(control.update(image, world_points=world).dragging)
                    image, world = observe(pointing_hand(), tilt, roll)
                    self.assertFalse(control.update(image, world_points=world).dragging)

    def test_missing_or_invalid_depth_releases_and_requires_open_hand_again(self):
        for invalid in ([], [(0., 0., 0.)] * 21, [(float('nan'), 0., 0.)] * 21, [(0., 0.)] * 21):
            with self.subTest(invalid=invalid):
                control = GestureController(Mock(return_value=0.))
                opened, open_world = observe(pointing_hand())
                closed, closed_world = observe(pointing_hand(True))
                control.update(opened, world_points=open_world)
                self.assertTrue(control.update(closed, world_points=closed_world).dragging)
                self.assertFalse(control.update(closed, world_points=invalid).dragging)
                self.assertFalse(control.update(closed, world_points=closed_world).dragging)
                control.update(opened, world_points=open_world)
                self.assertTrue(control.update(closed, world_points=closed_world).dragging)

    def test_session_moves_while_pointing_and_only_presses_for_actual_pinch(self):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((480, 640, 3))
        poses = [observe(pointing_hand(), tilt, aspect=4 / 3, offset=(tilt / 1000, 0.))
                 for tilt in (0., 60., 75., 85., 0.)]
        poses += [observe(pointing_hand(True), 75., aspect=4 / 3),
                  observe(pointing_hand(), 75., aspect=4 / 3)]
        tracker.detect.side_effect = [(points, world, WAIST) for points, world in poses]
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        stop = Mock(side_effect=[False] * len(poses) + [True])
        run_session(camera, tracker, pointer, view, policy, notify, stop, clock=Mock(return_value=0.))
        self.assertGreater(pointer.move.call_count, 1)
        pointer.press.assert_called_once()
        self.assertEqual([call.args[0] for call in notify.call_args_list], ['pinch', 'release'])
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
