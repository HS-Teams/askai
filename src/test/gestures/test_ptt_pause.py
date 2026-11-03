from io import StringIO
from threading import Event
import unittest
from unittest.mock import Mock, patch, call
import numpy as np

from askai.gestures import background
from askai.gestures.controller import GestureState
from askai.gestures.session import run_session
from askai.gestures.worker import read_controls
from landmark_fixtures import detection
from test_gestures import hand


class PttPauseTests(unittest.TestCase):
    def test_control_channel_changes_pause_without_stopping_worker(self):
        paused = Event()
        read_controls(StringIO('pause\n'), paused)
        self.assertTrue(paused.is_set())
        read_controls(StringIO('resume\n'), paused)
        self.assertFalse(paused.is_set())

    def test_absent_or_stopped_detector_is_not_started_by_ptt(self):
        for process in (None, Mock(poll=Mock(return_value=0))):
            with self.subTest(process=process), patch.object(background, '_process', process), patch.object(
                    background, 'launch') as launch:
                with background.pause_for_ptt():
                    pass
                launch.assert_not_called()
                if process is not None:
                    process.stdin.write.assert_not_called()

    def test_finishing_ptt_does_not_resume_replacement_worker(self):
        old = Mock(poll=Mock(return_value=None))
        replacement = Mock(poll=Mock(return_value=None))
        with patch.object(background, '_process', old):
            with background.pause_for_ptt():
                old.poll.return_value = 0
                background._process = replacement
        old.stdin.write.assert_called_once_with('pause\n')
        replacement.stdin.write.assert_not_called()

    def test_worker_exit_during_pause_request_does_not_break_ptt(self):
        process = Mock(poll=Mock(return_value=None))
        process.stdin.write.side_effect = BrokenPipeError
        with patch.object(background, '_process', process):
            with background.pause_for_ptt():
                pass

    def run_frames(self, samples, states):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        clock, paused = Mock(return_value=0), Mock(return_value=False)
        times = iter(samples)
        tracker.detect.return_value = detection(hand())
        calls_at = []

        def frame():
            now, is_paused = next(times)
            clock.return_value = now
            paused.return_value = is_paused
            return True, np.zeros((100, 100, 3))

        def preview(*args):
            camera.release.assert_not_called()
            tracker.close.assert_not_called()
            return True

        camera.read.side_effect = frame
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = preview
        notify.side_effect = lambda kind: calls_at.append((clock(), kind))
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = states
            run_session(camera, tracker, pointer, view, policy, notify=notify, clock=clock,
                        should_pause=paused, should_stop=Mock(side_effect=[False] * len(samples) + [True]))
            updated = controller.return_value.update.call_count
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()
        return pointer, calls_at, updated

    def test_long_ptt_blocks_commands_without_inactivity_shutdown(self):
        pointer, events, updated = self.run_frames([(0, True), (45, True), (60, True), (120, True)], [])
        self.assertEqual(events, [(0, 'ptt_paused')])
        self.assertEqual(updated, 0)
        for action in ('move', 'press', 'double_click', 'escape', 'scroll'):
            getattr(pointer, action).assert_not_called()
        self.assertEqual(pointer.release.call_count, 2)  # Enter pause, then final cleanup.

    def test_ptt_releases_drag_and_requires_fresh_resume_hold(self):
        pointer, events, updated = self.run_frames(
            [(0, False), (1, True), (120, True), (121, False), (123.499, False), (123.5, False)],
            [GestureState(dragging=True), GestureState(pointer=(.4, .4))])
        self.assertEqual(updated, 2)
        self.assertEqual(events, [(0, 'pinch'), (1, 'ptt_paused'), (123.5, 'resumed')])
        self.assertEqual(pointer.method_calls,
                         [call.press(), call.release(), call.release(), call.move(.4, .4), call.release()])
