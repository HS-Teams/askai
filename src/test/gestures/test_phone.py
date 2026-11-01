import unittest
from unittest.mock import Mock
from askai.gestures.controller import GestureController
from askai.gestures.phone import is_phone_hand


def phone():
    points = [(.5, .9)] * 21
    points[3], points[4] = (.3, .6), (.15, .3)
    for base, x in ((5, .35), (9, .45), (13, .55), (17, .65)):
        points[base:base+4] = [(x, .65), (x, .5), (x, .4), (x, .2 if base == 17 else .75)]
    return points


class PhoneTests(unittest.TestCase):
    def test_half_second_one_shot_and_rearm(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        self.assertTrue(is_phone_hand(phone(), 1))
        self.assertFalse(control.update(phone()).voice_requested)
        clock.return_value = .499
        self.assertFalse(control.update(phone()).voice_requested)
        clock.return_value = .5
        state = control.update(phone())
        self.assertTrue(state.voice_requested)
        self.assertIsNone(state.pointer)
        self.assertFalse(state.dragging)
        clock.return_value = 2.
        self.assertFalse(control.update(phone()).voice_requested)
        control.update([])
        self.assertEqual(control.update(phone()).voice_progress, 0)

    def test_extended_middle_finger_is_not_phone(self):
        points = phone()
        points[12] = (.45, .2)
        self.assertFalse(is_phone_hand(points, 1))
