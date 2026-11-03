import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.rock import is_rock_hand
from askai.gestures.preview import Pointer, Preview
from askai.gestures.session import run_session
from landmark_fixtures import detection, world_points
from test_escape import palm
from test_gestures import hand
from test_thumbs_up import thumbs_up


def rock():
    points = thumbs_up()
    points[4] = (.45, .7)
    points[8], points[20] = (.35, .2), (.65, .2)
    return points


class HandCommandTests(unittest.TestCase):
    def test_each_pose_waits_one_second_and_fires_once_until_released(self):
        for pose, field, progress in ((palm, 'double_click_requested', 'double_click_progress'),
                                      (rock, 'escape_requested', 'escape_progress')):
            with self.subTest(pose=pose.__name__):
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                points = pose()
                for time, expected in ((0., False), (.5, False), (.999, False), (1., True), (10., False)):
                    clock.return_value = time
                    state = control.update(points, world_points=world_points(points))
                    self.assertEqual(getattr(state, field), expected)
                    self.assertAlmostEqual(getattr(state, progress), min(time, 1.))
                    self.assertFalse(state.exit_requested)
                    self.assertFalse(state.dragging)
                    self.assertIsNone(state.pointer)
                    other = 'escape_requested' if pose is palm else 'double_click_requested'
                    self.assertFalse(getattr(state, other))
                control.update(hand(), world_points=world_points(hand()))
                self.assertFalse(getattr(control.update(points, world_points=world_points(points)), field))
                clock.return_value = 11.
                self.assertTrue(getattr(control.update(points, world_points=world_points(points)), field))

    def test_interruption_restarts_full_hold_for_both_commands(self):
        for pose, other, field in ((palm, rock, 'double_click_requested'), (rock, palm, 'escape_requested')):
            for interrupted in ([], hand(True), other()):
                with self.subTest(pose=pose.__name__, interrupted=interrupted):
                    clock = Mock(return_value=0.)
                    control = GestureController(clock)
                    points = pose()
                    control.update(points, world_points=world_points(points))
                    clock.return_value = .8
                    control.update(interrupted, world_points=world_points(interrupted))
                    clock.return_value = 1.
                    self.assertFalse(getattr(control.update(points, world_points=world_points(points)), field))
                    clock.return_value = 1.999
                    self.assertFalse(getattr(control.update(points, world_points=world_points(points)), field))
                    clock.return_value = 2.
                    self.assertTrue(getattr(control.update(points, world_points=world_points(points)), field))

    def test_thumb_and_incomplete_rock_are_not_heavy_metal(self):
        self.assertTrue(is_rock_hand(rock(), 1.))
        self.assertFalse(is_rock_hand(thumbs_up(), 1.))
        for tip in (8, 20):
            points = rock()
            points[tip] = (points[tip][0], .75)
            self.assertFalse(is_rock_hand(points, 1.))

    def test_native_double_click_sends_two_pairs_at_same_position_with_counts(self):
        pointer = Pointer.__new__(Pointer)
        pointer._pressed = False
        quartz = Mock()
        location = (350., 240.)
        quartz.CGEventGetLocation.return_value = location
        with patch.dict('sys.modules', Quartz=quartz), patch('askai.gestures.sfx.play_click') as sound:
            pointer.double_click()
        self.assertEqual([c.args[1] for c in quartz.CGEventCreateMouseEvent.call_args_list],
                         [quartz.kCGEventLeftMouseDown, quartz.kCGEventLeftMouseUp] * 2)
        self.assertTrue(all(c.args[2] == location for c in quartz.CGEventCreateMouseEvent.call_args_list))
        self.assertEqual([c.args[2] for c in quartz.CGEventSetIntegerValueField.call_args_list], [1, 1, 2, 2])
        self.assertEqual(quartz.CGEventPost.call_count, 4)
        self.assertEqual(sound.call_count, 2)

    def test_session_dispatches_each_command_once_after_hold(self):
        for pose, action in ((palm, 'double_click'), (rock, 'escape')):
            with self.subTest(pose=pose.__name__):
                camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
                clock = Mock(return_value=0.)
                times = iter((0., .999, 1., 2.))

                def frame():
                    clock.return_value = next(times)
                    return True, np.zeros((100, 100, 3))

                camera.read.side_effect = frame
                tracker.detect.return_value = detection(pose())
                view.prepare.side_effect = lambda image: image
                view.update.return_value = True
                stop = Mock(side_effect=[False] * 4 + [True])
                run_session(camera, tracker, pointer, view, policy, notify, stop, clock)
                getattr(pointer, action).assert_called_once_with()
                notify.assert_called_once_with(action)
                pointer.move.assert_not_called()
                pointer.press.assert_not_called()

    def test_preview_displays_correct_progress_instruction(self):
        cv = Mock()
        with patch.dict('sys.modules', cv2=cv, Quartz=Mock()):
            view = Preview(lambda text: text)
        view._escape_pressed = lambda: False
        cv.waitKey.return_value = -1
        cv.getWindowProperty.return_value = 1
        for state, label in ((GestureState(double_click_progress=.5), 'Hold open palm for 1s to double-click'),
                             (GestureState(escape_progress=.5), 'Hold heavy metal for 1s to send Esc')):
            view.update(np.zeros((100, 200, 3)), [], state)
            self.assertEqual(cv.putText.call_args.args[1], label + ' 50%')
