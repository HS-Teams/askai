from landmark_fixtures import POINTER_WAIST
from test_gestures import hand
from landmark_fixtures import detection, world_points
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.session import run_session


def palm():
    points = [(.5, .9)] * 21
    points[1:5] = [(.4, .75), (.3, .7), (.2, .65), (.1, .6)]
    for base, x in ((5, .35), (9, .45), (13, .55), (17, .65)):
        points[base:base+4] = [(x, .65), (x, .5), (x, .35), (x, .2)]
    return points


class EscapeTests(unittest.TestCase):
    def setUp(self):
        sound = patch('askai.gestures.sfx._play')
        sound.start()
        self.addCleanup(sound.stop)

    def test_one_double_click_per_palm_hold_without_escape_or_exit(self):
        clock = Mock(return_value=0.)
        controller = GestureController(clock)
        states = []
        for time in (0., .499, .5, 2.):
            clock.return_value = time
            states.append(controller.update(palm(), waist=POINTER_WAIST, world_points=world_points(palm())))
        self.assertEqual([s.double_click_requested for s in states], [False, False, True, False])
        self.assertTrue(all(s.pointer is None and not s.dragging and not s.exit_requested and not s.abort_requested for s in states))
        controller.update([], waist=POINTER_WAIST, world_points=world_points([]))
        clock.return_value = 3.
        self.assertFalse(controller.update(palm(), waist=POINTER_WAIST, world_points=world_points(palm())).double_click_requested)
        clock.return_value = 3.5
        self.assertTrue(controller.update(palm(), waist=POINTER_WAIST, world_points=world_points(palm())).double_click_requested)

    def test_abort_cancels_current_request_without_sending_keys_or_stopping_gestures(self):
        from types import SimpleNamespace
        from askai.gestures.command import abort_current_request
        shared, events, quartz = Mock(), Mock(), Mock()
        with patch.dict('sys.modules', {
                'askai.core.support.shared_instances': SimpleNamespace(shared=shared),
                'askai.core.askai_events': SimpleNamespace(events=events),
                'Quartz': quartz}), patch('askai.gestures.background.stop') as stop:
            abort_current_request()
            abort_current_request()
        self.assertEqual(shared.speech.cancel_output.call_count, 2)
        self.assertEqual(shared.mode.processor.cancel.call_count, 2)
        self.assertEqual(events.abort.emit.call_count, 2)
        events.abort.emit.assert_called_with(message='User interrupted [Heavy Metal]')
        stop.assert_not_called()
        quartz.CGEventCreateKeyboardEvent.assert_not_called()

    def test_session_requests_abort_and_continues(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = detection(hand())
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = [True, True, False]
        notify = Mock()
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [GestureState(abort_requested=True), GestureState(), GestureState()]
            run_session(camera, tracker, pointer, view, policy, notify=notify)
        notify.assert_called_once_with('abort')
        pointer.escape.assert_not_called()
        pointer.press.assert_not_called()
        self.assertEqual(camera.read.call_count, 3)
        pointer.release.assert_called()
