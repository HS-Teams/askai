from landmark_fixtures import POINTER_WAIST
from landmark_fixtures import world_points
import unittest
from unittest.mock import Mock
from askai.gestures.pointer_response import PointerResponse
from askai.gestures.controller import GestureController


def hand(x=.5):
    points = [(.5, .5)] * 21
    points[5], points[17] = (.4, .5), (.6, .5)
    points[8], points[4] = (x, .3), (x + .15, .3)
    return points


class PointerResponseTests(unittest.TestCase):
    def response_at_speed(self, speed):
        clock = Mock(return_value=0.)
        response = PointerResponse(.198, .008, clock)
        response.sample((0., 0.))
        values = []
        for i in range(1, 31):
            clock.return_value = i * .02
            values.append(response.sample((i * .02 * speed, 0.)))
        return values

    def test_fast_movement_increases_response_gradually(self):
        fast = self.response_at_speed(2.)
        slow = self.response_at_speed(.2)
        self.assertGreater(fast[-1], .198)
        self.assertLess(slow[-1], .198)
        self.assertTrue(all(abs(b-a) < .02 for a, b in zip(fast, fast[1:])))
        self.assertLessEqual(max(fast), .198 * 1.5)

    def test_stopping_reduces_response_smoothly_and_freezing_resets_it(self):
        clock = Mock(return_value=0.)
        response = PointerResponse(.198, .008, clock)
        response.sample((0., 0.))
        clock.return_value = .1
        fast = response.sample((.2, 0.))
        clock.return_value = .12
        slower = response.sample((.2, 0.))
        self.assertLess(slower, fast)
        self.assertGreater(slower, .198 * .5)
        self.assertEqual(response.sample((.9, 0.), frozen=True), .198)

    def test_absolute_target_does_not_overshoot_or_drift_when_hand_is_still(self):
        clock = Mock(return_value=0.)
        controller = GestureController(motion_clock=clock)
        previous = controller.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer[0]
        target = (.6 - controller.CAMERA_MARGIN) / (1 - 2 * controller.CAMERA_MARGIN)
        for i in range(1, 301):
            clock.return_value = i * .02
            current = controller.update(hand(.6), waist=POINTER_WAIST, world_points=world_points(hand(.6))).pointer[0]
            self.assertGreaterEqual(current, previous)
            self.assertLessEqual(current, target)
            self.assertLess(current - previous, .05)
            previous = current
        settled = previous
        for i in range(301, 321):
            clock.return_value = i * .02
            self.assertEqual(controller.update(hand(.6), waist=POINTER_WAIST, world_points=world_points(hand(.6))).pointer[0], settled)

    def test_small_hand_jitter_keeps_pointer_still(self):
        clock = Mock(return_value=0.)
        controller = GestureController(motion_clock=clock)
        initial = controller.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        for i in range(1, 51):
            clock.return_value = i * .02
            self.assertEqual(controller.update(hand(.5 + (-1)**i * .002), waist=POINTER_WAIST, world_points=world_points(hand(.5 + (-1)**i * .002))).pointer, initial)

    def test_tiny_pointer_adjustment_moves_only_a_fraction_of_normal_step(self):
        clock = Mock(return_value=0.)
        controller = GestureController(motion_clock=clock)
        initial = controller.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer[0]
        clock.return_value = .02
        adjusted = controller.update(hand(.506), waist=POINTER_WAIST, world_points=world_points(hand(.506))).pointer[0]
        normal_step = .012 * controller.SMOOTHING
        self.assertGreater(adjusted, initial)
        self.assertLess(adjusted - initial, normal_step * .08)

    def test_large_motion_keeps_normal_response(self):
        clock = Mock(return_value=0.)
        controller = GestureController(motion_clock=clock)
        initial = controller.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer[0]
        clock.return_value = .02
        moved = controller.update(hand(.6), waist=POINTER_WAIST, world_points=world_points(hand(.6))).pointer[0]
        self.assertGreater(moved - initial, .03)
