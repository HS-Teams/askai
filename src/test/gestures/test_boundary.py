import unittest
from unittest.mock import Mock, patch
import numpy as np
from landmark_fixtures import world_points
from askai.gestures.controller import GestureState
from askai.gestures.session import run_session
from askai.gestures.preview import Preview
from askai.gestures.waist import WaistBoundary
from test_gestures import hand
from test_escape import palm
from test_phone import phone
from test_scroll import fingers
from test_thumbs_up import thumbs_up
from test_rock import rock

WAIST = WaistBoundary((.3, .85), (.7, .85), 90.)


def run_frames(samples):
    """Samples are (time, preview hand points, unmirrored body boundary)."""
    camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
    clock = Mock(return_value=0.)
    frame = np.zeros((100, 100, 3))
    pending = iter(samples)

    def read():
        now, points, waist = next(pending)
        clock.return_value = now
        tracker.detect.return_value = ([(1-x, y) for x, y in points], world_points(points), waist)
        return True, frame

    camera.read.side_effect = read
    view.prepare.side_effect = lambda frame: frame
    view.update.return_value = True
    run_session(camera, tracker, pointer, view, policy, notify,
                should_stop=Mock(side_effect=[False] * len(samples) + [True]), clock=clock)
    return pointer, notify, [call.args[2] for call in view.update.call_args_list]


class GestureBoundaryTests(unittest.TestCase):
    def test_commands_work_above_line_and_are_blocked_on_or_below_it(self):
        for pose, field in ((palm, 'double_click_requested'), (rock, 'abort_requested'),
                            (phone, 'voice_requested'), (thumbs_up, 'exit_requested'), (fingers, 'scrolling')):
            for height in (.849, .85, .9):
                with self.subTest(pose=pose.__name__, height=height):
                    points = pose()
                    offset = height - max(points[4][1], points[8][1])
                    points = [(x, y + offset) for x, y in points]
                    samples = [(0, points, WAIST)]
                    if field != 'scrolling':
                        samples.append((1, points, WAIST))
                    _, _, states = run_frames(samples)
                    self.assertEqual(getattr(states[-1], field), height < .85)
                    if height >= .85:
                        self.assertEqual(states[-1], GestureState())

    def test_crossing_line_releases_drag_and_requires_new_pinch(self):
        for tip in (4, 8):
            with self.subTest(tip=tip):
                below = hand(True)
                below[tip] = (below[tip][0], .85)
                pointer, notify, states = run_frames([
                    (0, hand(), WAIST), (.1, hand(True), WAIST), (.2, below, WAIST),
                    (.3, hand(True), WAIST), (.4, hand(), WAIST), (1.2, hand(True), WAIST)])
                self.assertTrue(states[1].dragging)
                self.assertEqual(states[2], GestureState())
                self.assertFalse(states[3].dragging)
                self.assertEqual(states[4].pointer, states[0].pointer)
                self.assertTrue(states[5].dragging)
                self.assertEqual([c.args[0] for c in notify.call_args_list], ['pinch', 'release', 'pinch'])
                pointer.release.assert_called()

    def test_crossing_line_restarts_command_hold(self):
        below = [(x, y + .4) for x, y in palm()]
        pointer, _, states = run_frames([(0, palm(), WAIST), (.4, below, WAIST),
                                        (1, palm(), WAIST), (2, palm(), WAIST)])
        self.assertFalse(states[2].double_click_requested)
        self.assertTrue(states[3].double_click_requested)
        pointer.double_click.assert_called_once()

    def test_lowering_hand_stops_wheel_but_keeps_mode_during_exit_confirmation(self):
        below = [(x, y + .1) for x, y in fingers()]
        pointer, _, states = run_frames([(0, fingers(), WAIST), (.1, below, WAIST),
                                        (.599, below, WAIST), (.6, below, WAIST)])
        self.assertTrue(states[0].scrolling)
        self.assertEqual(states[1:3], [GestureState(scrolling=True)] * 2)
        self.assertEqual(states[3], GestureState())
        pointer.scroll.assert_not_called()
        pointer.move.assert_not_called()

    def test_missing_waist_blocks_commands_without_repeating_warning_on_flicker(self):
        pointer, notify, states = run_frames([(0, palm(), None), (1, palm(), None),
                                            (1.1, palm(), WAIST), (1.2, palm(), None), (2.2, palm(), None)])
        self.assertEqual([c.args[0] for c in notify.call_args_list], ['waist_missing'])
        pointer.double_click.assert_not_called()
        pointer.move.assert_not_called()
        self.assertEqual(states[-1], GestureState())

    def test_pause_at_two_and_half_seconds_and_resume_requires_visible_waist_for_two_and_half_seconds(self):
        _, notify, states = run_frames([(0, hand(), WAIST), (2.499, hand(), None),
            (2.5, hand(), None), (3, hand(), WAIST), (5, hand(), None),
            (6, hand(), WAIST), (8.499, hand(), WAIST), (8.5, hand(), WAIST)])
        self.assertEqual([c.args[0] for c in notify.call_args_list],
                         ['waist_missing', 'inactive', 'resumed'])
        self.assertIsNone(states[-2].pointer)
        self.assertIsNotNone(states[-1].pointer)

    def test_below_waist_counts_as_inactivity(self):
        below = [(x, y + .6) for x, y in hand()]
        _, notify, _ = run_frames([(0, hand(), WAIST), (2.5, below, WAIST)])
        notify.assert_called_once_with('inactive')

    def test_preview_draws_detected_sloped_line_and_no_fixed_fallback(self):
        cv = Mock()
        with patch.dict('sys.modules', cv2=cv, Quartz=Mock()):
            view = Preview(lambda text: text)
        view._escape_pressed = lambda: False
        cv.getWindowProperty.return_value = 1
        frame = np.zeros((100, 200, 3))
        waist = WaistBoundary((0, .6), (1, .8), 90.)
        for key in (-1, ord('['), ord(']')):
            cv.waitKey.return_value = key
            self.assertTrue(view.update(frame, [], GestureState(), waist))
            cv.line.assert_called_with(frame, (0, 60), (199, 80), (0, 200, 255), 2)
        cv.line.reset_mock()
        view.update(frame, [], GestureState(), None)
        cv.line.assert_not_called()
        self.assertIn('Waist not visible', cv.putText.call_args.args[1])
        cv.waitKey.return_value = 27
        self.assertFalse(view.update(frame, [], GestureState(), waist))
