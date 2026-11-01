import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.scroll import ScrollMotion, is_scroll_hand
from askai.gestures.session import run_session, authorize
from askai.core.permissions.grants import GrantPolicy, GrantDenied


def fingers():
    points = [(.5, .9)] * 21
    points[3], points[4] = (.3, .6), (.4, .8)
    for base, x in ((5, .35), (9, .45), (13, .55), (17, .65)):
        points[base:base+4] = [(x, .65), (x, .5), (x, .4), (x, .2 if base < 13 else .75)]
    return points


class ScrollTests(unittest.TestCase):
    def test_half_second_without_scroll_disables_mode(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        centered = [(x, y - .4) for x, y in fingers()]
        self.assertTrue(control.update(centered).scrolling)
        clock.return_value = .499
        self.assertTrue(control.update(centered).scrolling)
        clock.return_value = .5
        state = control.update(centered)
        self.assertFalse(state.scrolling)
        self.assertIsNone(state.pointer)
        clock.return_value = 1.1
        self.assertFalse(control.update(centered).scrolling)

    def test_missing_hand_times_out_scroll(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(fingers())
        clock.return_value = .5
        self.assertFalse(control.update([]).scrolling)


    def test_scroll_thumb_exit_requires_continuous_second_and_stops_scrolling(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(fingers())
        other = fingers()
        other[8] = (.35, .75)
        other[4] = (.8, .8)
        with patch('askai.gestures.controller.is_thumbs_up', return_value=True):
            first = control.update(other)
            self.assertTrue(first.scrolling)
            self.assertFalse(first.exit_requested)
            clock.return_value = .499
            self.assertFalse(control.update(other).exit_requested)
            clock.return_value = .5
            last = control.update(other)
            self.assertTrue(last.exit_requested)
            self.assertEqual(last.scroll_steps, 0)
            self.assertIsNone(last.pointer)

    def test_height_controls_continuous_scroll_and_edges(self):
        clock = Mock(return_value=0.)
        motion = ScrollMotion(clock)
        self.assertEqual(motion.update(.5), 0)
        clock.return_value = .2
        self.assertGreater(motion.update(.35), 0)
        clock.return_value = .4
        self.assertGreater(motion.update(.35), 0)
        clock.return_value = .6
        self.assertLess(motion.update(.65), 0)
        clock.return_value = .8
        self.assertEqual(motion.update(.5), 0)
        motion.update(.2)
        self.assertEqual(motion.boundary, 'top')
        motion.update(.2)
        self.assertIsNone(motion.boundary)
        motion.update(.8)
        self.assertEqual(motion.boundary, 'bottom')

    def test_toggle_requires_new_gesture_and_half_second_cooldown(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        self.assertTrue(control.update(fingers()).scrolling)
        other = fingers()
        other[8] = (.35, .75)
        other[4] = (.8, .8)
        clock.return_value = .2
        self.assertTrue(control.update(other).scrolling)
        clock.return_value = .3
        self.assertTrue(control.update(fingers()).scrolling)
        clock.return_value = .6
        self.assertTrue(control.update(fingers()).scrolling)
        control.update(other)
        self.assertFalse(control.update(fingers()).scrolling)
        clock.return_value = .7
        self.assertIsNone(control.update(other).pointer)
        clock.return_value = 1.2
        self.assertIsNotNone(control.update(other).pointer)

    def test_active_scroll_ignores_palm_but_checks_thumbs_up(self):
        control = GestureController(Mock(return_value=0.))
        control.update(fingers())
        other = fingers()
        other[8] = (.35, .75)
        other[4] = (.8, .8)
        with patch('askai.gestures.controller.is_thumbs_up', return_value=False) as thumbs, patch(
                'askai.gestures.controller.is_open_palm') as palm:
            state = control.update([(x, y - .06) for x, y in other])
        thumbs.assert_called_once()
        palm.assert_not_called()
        self.assertTrue(state.scrolling)
        self.assertEqual(state.scroll_steps, 0)
        self.assertIsNone(state.pointer)
        self.assertFalse(state.dragging)

    def test_hand_loss_preserves_mode_without_retrigger_or_scroll_jump(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(fingers())
        self.assertTrue(control.update([]).scrolling)
        clock.return_value = .2
        state = control.update([(x, y - .2) for x, y in fingers()])
        self.assertTrue(state.scrolling)
        self.assertEqual(state.scroll_steps, 0)


    def test_only_two_extended_fingers_select_scroll(self):
        self.assertTrue(is_scroll_hand(fingers(), 1))
        for index, position in ((8, (.35, .75)), (12, (.45, .75)), (16, (.55, .2)),
                                (20, (.65, .2)), (4, (.3, .2))):
            points = fingers()
            points[index] = position
            self.assertFalse(is_scroll_hand(points, 1))

    def test_neutral_zone_and_rate_limit(self):
        clock = Mock(return_value=0.)
        motion = ScrollMotion(clock)
        motion.update(.5)
        for y in (.51, .49, .505, .495):
            clock.return_value += .2
            self.assertEqual(motion.update(y), 0)
        clock.return_value += .2
        self.assertGreater(motion.update(.3), 0)
        self.assertEqual(motion.update(.3), 0)

    def test_controller_freezes_pointer_and_disallows_clicks(self):
        control = GestureController()
        state = control.update(fingers())
        self.assertTrue(state.scrolling)
        moved = [(x, y - .06) for x, y in fingers()]
        state = control.update(moved)
        self.assertEqual(state.scroll_steps, 0)
        self.assertIsNone(state.pointer)
        self.assertFalse(state.dragging)
        control.update([])
        self.assertEqual(control.update(moved).scroll_steps, 0)

    def test_scroll_denial_prevents_start(self):
        policy = GrantPolicy(lambda key: 'deny' if key.endswith('desktop.pointer.scroll') else 'allow')
        with self.assertRaises(GrantDenied):
            authorize(policy, Mock())

    def test_session_emits_direction_changes_not_every_frame(self):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = []
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = [True] * 5 + [False]
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [GestureState(scrolling=True, scroll_steps=n)
                for n in (0, 1, 2, -1)] + [GestureState(), GestureState()]
            run_session(camera, tracker, pointer, view, policy, notify=notify)
        self.assertEqual([c.args[0] for c in notify.call_args_list],
                         ['scroll_start', 'scroll_up', 'scroll_down', 'scroll_stop'])
        self.assertEqual([c.args[0] for c in pointer.scroll.call_args_list], [1, 2, -1])
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
