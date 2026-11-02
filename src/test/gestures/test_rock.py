import unittest
from unittest.mock import Mock, patch
from askai.gestures.controller import GestureController
from askai.gestures.rock import is_rock_hand
from askai.gestures.preview import Pointer
from test_thumbs_up import thumbs_up


def rock():
    points = thumbs_up()
    points[4] = (.45, .7)
    points[8], points[20] = (.35, .2), (.65, .2)
    return points


class RockTests(unittest.TestCase):
    def test_rock_stops_after_existing_hold_without_double_click(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        self.assertTrue(is_rock_hand(rock(), 1.))
        self.assertFalse(control.update(rock()).exit_requested)
        clock.return_value = .499
        self.assertFalse(control.update(rock()).exit_requested)
        clock.return_value = .5
        state = control.update(rock())
        self.assertTrue(state.exit_requested)
        self.assertFalse(state.double_click_requested)

    def test_thumb_and_incomplete_rock_are_not_exit(self):
        self.assertFalse(is_rock_hand(thumbs_up(), 1.))
        for tip in (8, 20):
            points = rock()
            points[tip] = (points[tip][0], .75)
            self.assertFalse(is_rock_hand(points, 1.))

    def test_held_thumb_only_double_clicks_once(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(thumbs_up())
        clock.return_value = .5
        state = control.update(thumbs_up())
        self.assertTrue(state.double_click_requested)
        self.assertFalse(state.exit_requested)
        clock.return_value = 2.
        self.assertFalse(control.update(thumbs_up()).double_click_requested)

    def test_native_double_click_emits_two_pairs_with_correct_counts(self):
        pointer = Pointer.__new__(Pointer)
        pointer._pressed = False
        quartz = Mock()
        with patch.dict('sys.modules', Quartz=quartz), patch('askai.gestures.sfx.play_click') as sound:
            pointer.double_click()
        self.assertEqual([c.args[2] for c in quartz.CGEventSetIntegerValueField.call_args_list], [1, 1, 2, 2])
        self.assertEqual(quartz.CGEventPost.call_count, 4)
        self.assertEqual(sound.call_count, 2)
