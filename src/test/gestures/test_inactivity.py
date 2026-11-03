from landmark_fixtures import detection, WAIST
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
        clock = Mock(return_value=0.)
        times = iter((5, 8, 19.999))

        def capture():
            clock.return_value = next(times)
            return True, np.zeros((100, 100, 3))

        camera.read.side_effect = capture
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
                    clock=clock)
        self.assertEqual(view.update.call_count, 3)
        notify.assert_called_once_with('inactive')
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()

    def run_frames(self, times, hands, waists=None, *, auto_stop=False):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        clock = Mock(return_value=times[0])
        samples = iter(zip(times[1:], hands, waists if waists is not None else [WAIST] * len(hands)))
        self.events_at = []
        notify.side_effect = lambda kind: self.events_at.append((clock(), kind))

        def frame():
            now, points, waist = next(samples)
            clock.return_value = now
            tracker.detect.return_value = (*detection(points)[:2], waist)
            return True, np.zeros((100, 100, 3))

        camera.read.side_effect = frame
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        stop = Mock(side_effect=[False] * len(hands) + [True])
        run_session(camera, tracker, pointer, view, policy, notify=notify,
                    should_stop=stop, clock=clock)
        for resource, method in ((camera, 'release'), (tracker, 'close'), (view, 'close')):
            getattr(resource, method).assert_called_once()
        pointer.release.assert_called()
        self.assertEqual(camera.read.call_count, len(hands))
        self.assertEqual(stop.call_count, len(hands) if auto_stop else len(hands) + 1)
        self.assertEqual(view.update.call_count, len(hands) - 1 if auto_stop else len(hands))
        return pointer, notify

    def test_no_hand_enters_standby_once_and_keeps_capturing(self):
        pointer, notify = self.run_frames([0, 2.499, 2.5, 3, 17.499], [[], [], [], []])
        notify.assert_called_once_with('inactive')
        pointer.press.assert_not_called()
        pointer.move.assert_not_called()

    def test_normal_pointer_hand_resets_inactivity(self):
        _, notify = self.run_frames([0, 2.4, 4.899, 4.9], [hand(), [], []])
        notify.assert_called_once_with('inactive')

    def test_invalid_landmarks_do_not_prevent_standby(self):
        _, notify = self.run_frames([0, 6, 7], [[(float('nan'), .5)] * 21, []])
        notify.assert_called_once_with('inactive')

    def test_hand_resumes_after_two_and_half_seconds_and_can_wait_again(self):
        pointer, notify = self.run_frames([0, 5, 6, 8.499, 8.5, 10, 15],
                                        [[], hand(), hand(), hand(), hand(), []])
        self.assertEqual([call.args[0] for call in notify.call_args_list],
                         ['inactive', 'resumed', 'inactive'])
        self.assertEqual(pointer.move.call_count, 2)
        pointer.press.assert_not_called()

    def test_brief_reappearance_does_not_move_or_resume(self):
        pointer, notify = self.run_frames([0, 5, 6, 8.499], [[], hand(), hand()])
        notify.assert_called_once_with('inactive')
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()

    def test_missing_or_invalid_hand_restarts_two_and_half_second_hold(self):
        for lost in ([], [(float('nan'), .5)] * 21):
            with self.subTest(lost=lost):
                pointer, notify = self.run_frames(
                    [0, 5, 6, 8, 8.5, 10, 10.999, 11],
                    [[], hand(), lost, hand(), hand(), hand(), hand()])
                self.assertEqual([call.args[0] for call in notify.call_args_list], ['inactive', 'resumed'])
                self.assertEqual(pointer.move.call_count, 1)
                pointer.press.assert_not_called()

    def test_command_pose_does_not_fire_during_resume_hold(self):
        from test_escape import palm
        pointer, notify = self.run_frames([0, 5, 6, 8.499], [[], palm(), palm()])
        notify.assert_called_once_with('inactive')
        pointer.escape.assert_not_called()
        pointer.double_click.assert_not_called()
        pointer.scroll.assert_not_called()
        pointer.move.assert_not_called()

    def test_warning_at_forty_five_seconds_of_pause_and_shutdown_at_sixty(self):
        pointer, notify = self.run_frames([0, 2.499, 2.5, 47.499, 47.5, 48, 62.499, 62.5], [[]] * 7, auto_stop=True)
        self.assertEqual(self.events_at, [(2.5, 'inactive'), (47.5, 'inactivity_warning')])
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
        pointer.double_click.assert_not_called()
        pointer.escape.assert_not_called()
        pointer.scroll.assert_not_called()

    def test_pause_warning_and_shutdown_apply_to_every_pause_reason(self):
        below = [(x, y + .8) for x, y in hand()]
        for points, waist in (([], WAIST), ([(float('nan'), .5)] * 21, WAIST),
                              (below, WAIST), (hand(), None)):
            with self.subTest(points=points, waist=waist):
                pointer, notify = self.run_frames([0, 2.499, 2.5, 47.5, 62.5],
                                                  [points] * 4, [waist] * 4, auto_stop=True)
                timed_events = [(time, event) for time, event in self.events_at if event != 'waist_missing']
                self.assertEqual(timed_events, [(2.5, 'inactive'), (47.5, 'inactivity_warning')])
                pointer.move.assert_not_called()

    def test_switching_pause_reason_does_not_restart_shutdown_countdown(self):
        below = [(x, y + .8) for x, y in hand()]
        _, notify = self.run_frames([0, 2.5, 5, 10, 47.5, 62.5],
                                    [[], hand(), below, [], hand()], [WAIST, None, WAIST, WAIST, None], auto_stop=True)
        self.assertEqual([entry for entry in self.events_at if entry[1] != 'waist_missing'],
                         [(2.5, 'inactive'), (47.5, 'inactivity_warning')])

    def test_brief_reappearance_does_not_cancel_pending_shutdown(self):
        pointer, notify = self.run_frames([0, 2.5, 47.5, 60.1, 62.499, 62.5],
                                         [[], [], hand(), hand(), hand()], auto_stop=True)
        self.assertEqual(self.events_at, [(2.5, 'inactive'), (47.5, 'inactivity_warning')])
        pointer.move.assert_not_called()

    def test_successful_resume_cancels_countdown_and_next_pause_warns_again(self):
        _, notify = self.run_frames([0, 2.5, 47.5, 48, 50.499, 50.5, 53, 97.999, 98, 113],
                                    [[], [], hand(), hand(), hand(), [], [], [], []], auto_stop=True)
        self.assertEqual(self.events_at, [(2.5, 'inactive'), (47.5, 'inactivity_warning'),
                         (50.5, 'resumed'), (53, 'inactive'), (98, 'inactivity_warning')])

    def test_valid_stationary_hand_does_not_count_as_pause(self):
        _, notify = self.run_frames([0, 10, 20, 30, 60], [hand()] * 4)
        notify.assert_not_called()

    def test_late_frame_stops_without_promising_another_fifteen_seconds(self):
        _, notify = self.run_frames([0, 2.5, 65], [[], []], auto_stop=True)
        notify.assert_called_once_with('inactive')

    def test_resume_cannot_override_shutdown_deadline(self):
        pointer, notify = self.run_frames([0, 2.5, 47.5, 60, 62.5],
                                         [[], [], hand(), hand()], auto_stop=True)
        self.assertEqual(self.events_at, [(2.5, 'inactive'), (47.5, 'inactivity_warning')])
        pointer.move.assert_not_called()

    def test_waist_flicker_warns_once_during_pause_and_preserves_shutdown_warning(self):
        times = [0, 0, 2.5, 3, 3.1, 4, 4.1, 10, 10.1, 47.5, 62.5]
        waists = [None, None, WAIST, None, WAIST, None, WAIST, None, None, None]
        self.run_frames(times, [hand()] * 10, waists, auto_stop=True)
        self.assertEqual(self.events_at, [(0, 'waist_missing'), (2.5, 'inactive'), (47.5, 'inactivity_warning')])

    def test_waist_warning_rearms_only_after_stable_control_recovery(self):
        times = [0, 0, .1, 2.599, 2.6, 3, 5.499, 5.5, 5.6]
        waists = [None, WAIST, WAIST, None, WAIST, WAIST, WAIST, None]
        self.run_frames(times, [hand()] * 8, waists)
        self.assertEqual(self.events_at, [(0, 'waist_missing'), (5.6, 'waist_missing')])

    def test_visible_body_without_valid_hand_does_not_rearm_warning(self):
        self.run_frames([0, 0, 2.5, 3, 6, 7], [hand(), [], [], [], hand()],
                        [None, WAIST, WAIST, WAIST, None])
        self.assertEqual(self.events_at, [(0, 'waist_missing'), (2.5, 'inactive')])
