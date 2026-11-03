from landmark_fixtures import POINTER_WAIST
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
    def test_projected_rock_does_not_abort_when_middle_and_ring_are_extended_in_depth(self):
        points = rock()
        spatial = world_points(points)
        for tip in (12, 16):
            x, y, _ = spatial[tip]
            spatial[tip] = (x, y, .08)
        self.assertFalse(is_rock_hand(spatial))
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        for time in (0., .5, 2.):
            clock.return_value = time
            state = control.update(points, waist=POINTER_WAIST, world_points=spatial)
            self.assertFalse(state.abort_requested)
            self.assertIsNone(state.abort_progress)

    def test_real_rock_uses_3d_shape_when_wrist_rotates(self):
        from math import sin, cos, radians
        for tilt in (-75., -45., 0., 45., 75.):
            with self.subTest(tilt=tilt):
                angle = radians(tilt)
                spatial = [(x, y*cos(angle), y*sin(angle)) for x, y, _ in world_points(rock())]
                points = [(x/.1, y/.1) for x, y, _ in spatial]
                self.assertTrue(is_rock_hand(spatial))
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                self.assertFalse(control.update(points, waist=POINTER_WAIST, world_points=spatial).abort_requested)
                clock.return_value = .5
                self.assertTrue(control.update(points, waist=POINTER_WAIST, world_points=spatial).abort_requested)

    def test_each_pose_waits_half_second_and_fires_once_until_released(self):
        for pose, field, progress in ((palm, 'double_click_requested', 'double_click_progress'),
                                      (rock, 'abort_requested', 'abort_progress')):
            with self.subTest(pose=pose.__name__):
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                points = pose()
                for time, expected in ((0., False), (.499, False), (.5, True), (10., False)):
                    clock.return_value = time
                    state = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
                    self.assertEqual(getattr(state, field), expected)
                    self.assertAlmostEqual(getattr(state, progress), min(time / .5, 1.))
                    self.assertFalse(state.exit_requested)
                    self.assertFalse(state.dragging)
                    self.assertIsNone(state.pointer)
                    other = 'abort_requested' if pose is palm else 'double_click_requested'
                    self.assertFalse(getattr(state, other))
                control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
                self.assertFalse(getattr(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)), field))
                clock.return_value = 11.
                self.assertTrue(getattr(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)), field))

    def test_interruption_restarts_full_hold_for_both_commands(self):
        for pose, other, field in ((palm, rock, 'double_click_requested'), (rock, palm, 'abort_requested')):
            for interrupted in ([], hand(True), other()):
                with self.subTest(pose=pose.__name__, interrupted=interrupted):
                    clock = Mock(return_value=0.)
                    control = GestureController(clock)
                    points = pose()
                    control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
                    clock.return_value = .8
                    control.update(interrupted, waist=POINTER_WAIST, world_points=world_points(interrupted))
                    clock.return_value = 1.
                    self.assertFalse(getattr(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)), field))
                    clock.return_value = 1.499
                    self.assertFalse(getattr(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)), field))
                    clock.return_value = 1.5
                    self.assertTrue(getattr(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)), field))

    def test_thumb_and_incomplete_rock_are_not_heavy_metal(self):
        self.assertTrue(is_rock_hand(world_points(rock())))
        self.assertFalse(is_rock_hand(world_points(thumbs_up())))
        for tip in (8, 20):
            points = rock()
            points[tip] = (points[tip][0], .75)
            self.assertFalse(is_rock_hand(world_points(points)))

    def test_native_double_click_sends_two_pairs_at_same_position_with_counts(self):
        pointer = Pointer.__new__(Pointer)
        pointer._pressed = False
        quartz = Mock()
        location = (350., 240.)
        quartz.CGEventGetLocation.return_value = location
        with patch.dict('sys.modules', Quartz=quartz), patch('askai.gestures.sfx.play_double_click') as sound, patch(
                'askai.gestures.sfx.play_click') as single_click:
            sound.side_effect = lambda: self.assertEqual(quartz.CGEventPost.call_count, 4)
            pointer.double_click()
        self.assertEqual([c.args[1] for c in quartz.CGEventCreateMouseEvent.call_args_list],
                         [quartz.kCGEventLeftMouseDown, quartz.kCGEventLeftMouseUp] * 2)
        self.assertTrue(all(c.args[2] == location for c in quartz.CGEventCreateMouseEvent.call_args_list))
        self.assertEqual([c.args[2] for c in quartz.CGEventSetIntegerValueField.call_args_list], [1, 1, 2, 2])
        self.assertEqual(quartz.CGEventPost.call_count, 4)
        sound.assert_called_once_with()
        single_click.assert_not_called()

    def test_session_dispatches_each_command_once_after_hold(self):
        for pose, action in ((palm, 'double_click'), (rock, 'abort')):
            with self.subTest(pose=pose.__name__):
                camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
                clock = Mock(return_value=0.)
                times = iter((0., .499, .5, 2.))

                def frame():
                    clock.return_value = next(times)
                    return True, np.zeros((100, 100, 3))

                camera.read.side_effect = frame
                tracker.detect.return_value = detection(pose())
                view.prepare.side_effect = lambda image: image
                view.update.return_value = True
                stop = Mock(side_effect=[False] * 4 + [True])
                run_session(camera, tracker, pointer, view, policy, notify, stop, clock)
                if action == 'double_click':
                    pointer.double_click.assert_called_once_with()
                pointer.escape.assert_not_called()
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
        for state, label in ((GestureState(double_click_progress=.5), 'Hold open palm for 0.5s to double-click'),
                             (GestureState(abort_progress=.5), 'Hold heavy metal for 0.5s to abort')):
            view.update(np.zeros((100, 200, 3)), [], state)
            self.assertEqual(cv.putText.call_args.args[1], label + ' 50%')
