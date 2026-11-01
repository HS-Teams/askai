import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.thumbs_up import is_thumbs_up
from askai.gestures.session import run_session
from askai.gestures.preview import Preview


def thumbs_up():
    points = [(.5, .9)] * 21
    points[1:5] = [(.35, .75), (.3, .6), (.3, .4), (.3, .2)]
    for base, x in ((5, .35), (9, .45), (13, .55), (17, .65)):
        points[base:base + 4] = [(x, .65), (x, .5), (x, .65), (x, .75)]
    return points


class ThumbsUpTests(unittest.TestCase):
    def test_diagonal_thumb_is_not_up(self):
        points = thumbs_up()
        points[2], points[3], points[4] = (.3, .6), (.4, .4), (.5, .2)
        self.assertFalse(is_thumbs_up(points, 1))

    def test_gesture_must_remain_strictly_up_for_full_second(self):
        clock = Mock(side_effect=[0, .4, 1., 1.499, 1.5])
        control = GestureController(clock)
        control.update(thumbs_up())
        self.assertFalse(control.update(thumbs_up()).exit_requested)
        diagonal = thumbs_up()
        diagonal[2], diagonal[3], diagonal[4] = (.3, .6), (.4, .4), (.5, .2)
        self.assertIsNone(control.update(diagonal).exit_progress)
        self.assertFalse(control.update(thumbs_up()).exit_requested)
        self.assertFalse(control.update(thumbs_up()).exit_requested)
        self.assertTrue(control.update(thumbs_up()).exit_requested)


    def test_hold_uses_elapsed_time_and_never_moves_or_clicks(self):
        clock = Mock(side_effect=[10, 10.25, 10.499, 10.5])
        control = GestureController(clock)
        states = [control.update(thumbs_up()) for _ in range(4)]
        self.assertEqual(states[0].exit_progress, 0)
        self.assertEqual(states[1].exit_progress, .5)
        self.assertFalse(states[2].exit_requested)
        self.assertTrue(states[3].exit_requested)
        self.assertTrue(all(s.pointer is None and not s.dragging for s in states))

    def test_missing_hand_restarts_countdown(self):
        control = GestureController(Mock(side_effect=[0, .8, 2]))
        control.update(thumbs_up())
        control.update(thumbs_up())
        control.update([])
        self.assertEqual(control.update(thumbs_up()).exit_progress, 0)

    def test_extended_finger_cancels_confirmation(self):
        for tip in (8, 12, 16, 20):
            control = GestureController(Mock(return_value=0.))
            control.update(thumbs_up())
            points = thumbs_up()
            points[tip] = (points[tip][0], .2)
            self.assertFalse(is_thumbs_up(points, 1))
            self.assertIsNone(control.update(points).exit_progress)
            self.assertEqual(control.update(thumbs_up()).exit_progress, 0)

    def test_open_palm_does_not_exit(self):
        points = thumbs_up()
        for tip in (8, 12, 16, 20):
            points[tip] = (points[tip][0], .2)
        self.assertIsNone(GestureController().update(points).exit_progress)

    def test_downward_and_sideways_thumb_do_not_exit(self):
        for points in ([(x, 1-y) for x, y in thumbs_up()],
                       [(y, 1-x) for x, y in thumbs_up()]):
            self.assertFalse(is_thumbs_up(points, 1))

    def test_mirrored_right_hand_is_recognized(self):
        self.assertTrue(is_thumbs_up([(1-x, y) for x, y in thumbs_up()], 1.5))

    def test_session_exits_without_mouse_actions_and_releases_resources(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = thumbs_up()
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [
                GestureState(exit_progress=0), GestureState(exit_progress=1, exit_requested=True)]
            run_session(camera, tracker, pointer, view, policy)
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()

    def test_preview_draws_progress(self):
        view = Preview.__new__(Preview)
        view.cv = Mock()
        view._initial_resize_pending = False
        view.cv.waitKey.return_value = -1
        view.cv.getWindowProperty.return_value = 1
        view._escape_pressed = lambda: False
        view._labels = {key: key for key in ('No hand', 'Esc: stop', 'Hold thumbs up to stop')}
        self.assertTrue(view.update(np.zeros((100, 200, 3)), [], GestureState(exit_progress=.5)))
        self.assertEqual(view.cv.rectangle.call_count, 2)
        self.assertIn('50%', view.cv.putText.call_args.args[1])
