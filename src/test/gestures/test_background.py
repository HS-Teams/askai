import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
from askai.gestures import background
from askai.gestures.session import run_session
from askai.gestures.controller import GestureState
import numpy as np


class BackgroundTests(unittest.TestCase):
    def test_worker_logs_to_file_and_keeps_events_separate(self):
        process = Mock(pid=123)
        with TemporaryDirectory() as storage, patch.object(background, '_process', None), patch.object(
                background.subprocess, 'Popen', return_value=process) as popen, patch.object(background, 'Thread') as thread:
            result = background.launch(1, storage, {}, Mock())
            self.assertEqual(result['status'], 'starting')
            self.assertTrue(Path(result['log']).is_file())
            kwargs = popen.call_args.kwargs
            self.assertIs(kwargs['stdout'], kwargs['stderr'])
            self.assertTrue(kwargs['start_new_session'])
            self.assertEqual(len(kwargs['pass_fds']), 1)
            # No reader was started by the mocked Thread.
            os.close(thread.call_args.kwargs['args'][0])

    def test_duplicate_worker_is_rejected(self):
        with patch.object(background, '_process', Mock(poll=Mock(return_value=None))):
            with self.assertRaises(RuntimeError):
                background.launch(0, '.', {}, Mock())

    def test_pipe_delivers_recognition_and_completion(self):
        read_fd, write_fd = os.pipe()
        with os.fdopen(write_fd, 'w') as output:
            output.write(json.dumps('pinch') + '\n')
        notify = Mock()
        background._read_events(read_fd, Mock(wait=Mock(return_value=0)), notify)
        self.assertEqual([call.args[0] for call in notify.call_args_list], ['pinch', 'stopped'])

    def test_shutdown_only_terminates_owned_worker(self):
        process = Mock(poll=Mock(return_value=None))
        with patch.object(background, '_process', process):
            background.stop()
        process.terminate.assert_called_once()
        process.wait.assert_called_once_with(timeout=5)
        process.kill.assert_not_called()


class RecognitionEventsTests(unittest.TestCase):
    def test_events_are_transitions_not_per_frame(self):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = []
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = [True] * 5 + [False]
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [
                GestureState(dragging=True), GestureState(dragging=True),
                GestureState(), GestureState(), GestureState(escape_requested=True), GestureState()]
            run_session(camera, tracker, pointer, view, policy, notify=notify)
        self.assertEqual([call.args[0] for call in notify.call_args_list], ['pinch', 'release', 'escape'])

    def test_parent_shutdown_releases_resources(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        run_session(camera, tracker, pointer, view, policy, should_stop=lambda: True)
        camera.read.assert_not_called()
        pointer.release.assert_called_once()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()
