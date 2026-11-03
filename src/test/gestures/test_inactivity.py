from landmark_fixtures import detection
import unittest
from unittest.mock import Mock
import numpy as np
from askai.gestures.session import run_session


def hand():
    points = [(.5, .5)] * 21
    points[5], points[17] = (.4, .5), (.6, .5)
    points[4], points[8] = (.7, .3), (.5, .3)
    return points


class InactivityTests(unittest.TestCase):
    def test_preview_can_close_while_paused_and_resources_stay_open_until_then(self):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((100, 100, 3))
        tracker.detect.return_value = detection([])
        view.prepare.side_effect = lambda frame: frame
        frames = iter((True, True, False))

        def preview(*_):
            camera.release.assert_not_called()
            tracker.close.assert_not_called()
            view.close.assert_not_called()
            return next(frames)

        view.update.side_effect = preview
        run_session(camera, tracker, pointer, view, policy, notify=notify,
                    clock=Mock(side_effect=[0, 5, 8, 20]))
        self.assertEqual(view.update.call_count, 3)
        notify.assert_called_once_with('inactive')
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()

    def run_frames(self, times, hands):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((100, 100, 3))
        tracker.detect.side_effect = [detection(points) for points in hands]
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        stop = Mock(side_effect=[False] * len(hands) + [True])
        run_session(camera, tracker, pointer, view, policy, notify=notify,
                    should_stop=stop, clock=Mock(side_effect=times))
        for resource, method in ((camera, 'release'), (tracker, 'close'), (view, 'close')):
            getattr(resource, method).assert_called_once()
        pointer.release.assert_called()
        self.assertEqual(camera.read.call_count, len(hands))
        return pointer, notify

    def test_no_hand_enters_standby_once_and_keeps_capturing(self):
        pointer, notify = self.run_frames([0, 2.499, 2.5, 3, 20], [[], [], [], []])
        notify.assert_called_once_with('inactive')
        pointer.press.assert_not_called()
        pointer.move.assert_not_called()

    def test_normal_pointer_hand_resets_inactivity(self):
        _, notify = self.run_frames([0, 2.4, 4.899, 4.9], [hand(), [], []])
        notify.assert_called_once_with('inactive')

    def test_invalid_landmarks_do_not_prevent_standby(self):
        _, notify = self.run_frames([0, 6, 7], [[(float('nan'), .5)] * 21, []])
        notify.assert_called_once_with('inactive')

    def test_hand_resumes_after_three_seconds_and_can_wait_again(self):
        pointer, notify = self.run_frames([0, 5, 6, 8.999, 9, 10, 15],
                                        [[], hand(), hand(), hand(), hand(), []])
        self.assertEqual([call.args[0] for call in notify.call_args_list],
                         ['inactive', 'resumed', 'inactive'])
        self.assertEqual(pointer.move.call_count, 2)
        pointer.press.assert_not_called()

    def test_brief_reappearance_does_not_move_or_resume(self):
        pointer, notify = self.run_frames([0, 5, 6, 8.999], [[], hand(), hand()])
        notify.assert_called_once_with('inactive')
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()

    def test_missing_or_invalid_hand_restarts_three_second_hold(self):
        for lost in ([], [(float('nan'), .5)] * 21):
            with self.subTest(lost=lost):
                pointer, notify = self.run_frames(
                    [0, 5, 6, 8, 8.5, 10, 11.499, 11.5],
                    [[], hand(), lost, hand(), hand(), hand(), hand()])
                self.assertEqual([call.args[0] for call in notify.call_args_list], ['inactive', 'resumed'])
                self.assertEqual(pointer.move.call_count, 1)
                pointer.press.assert_not_called()

    def test_command_pose_does_not_fire_during_resume_hold(self):
        from test_escape import palm
        pointer, notify = self.run_frames([0, 5, 6, 8.9], [[], palm(), palm()])
        notify.assert_called_once_with('inactive')
        pointer.escape.assert_not_called()
        pointer.double_click.assert_not_called()
        pointer.scroll.assert_not_called()
        pointer.move.assert_not_called()
