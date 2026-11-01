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
    def run_frames(self, times, hands):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((100, 100, 3))
        tracker.detect.side_effect = hands
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        # Controller does not consult the clock for an ordinary open hand or no hand.
        run_session(camera, tracker, pointer, view, policy, notify=notify, clock=Mock(side_effect=times))
        for resource, method in ((camera, 'release'), (tracker, 'close'), (view, 'close')):
            getattr(resource, method).assert_called_once()
        pointer.release.assert_called()
        return camera, notify

    def test_no_hand_stops_only_after_five_seconds(self):
        camera, notify = self.run_frames([0, 5, 5.001], [[], []])
        self.assertEqual(camera.read.call_count, 2)
        notify.assert_called_once_with('inactive')

    def test_normal_pointer_hand_resets_inactivity(self):
        camera, notify = self.run_frames([0, 4.9, 9.9, 9.901], [hand(), [], []])
        self.assertEqual(camera.read.call_count, 3)
        notify.assert_called_once_with('inactive')

    def test_invalid_landmarks_do_not_keep_session_alive(self):
        _, notify = self.run_frames([0, 6], [[(float('nan'), .5)] * 21])
        notify.assert_called_once_with('inactive')
