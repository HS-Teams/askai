from test_gestures import hand
from landmark_fixtures import detection, world_points
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.preview import Pointer
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
        controller = GestureController(Mock(side_effect=[0, .999, 1., 2, 3, 4]))
        states = [controller.update(palm(), world_points=world_points(palm())) for _ in range(4)]
        self.assertEqual([s.double_click_requested for s in states], [False, False, True, False])
        self.assertTrue(all(s.pointer is None and not s.dragging and not s.exit_requested and not s.escape_requested for s in states))
        controller.update([], world_points=world_points([]))
        self.assertFalse(controller.update(palm(), world_points=world_points(palm())).double_click_requested)
        self.assertTrue(controller.update(palm(), world_points=world_points(palm())).double_click_requested)

    def test_escape_is_delivered_to_same_focused_app_key_down_and_up(self):
        quartz, appkit = Mock(), Mock()
        appkit.NSWorkspace.sharedWorkspace.return_value.frontmostApplication.return_value.processIdentifier.return_value = 123
        quartz.CGEventCreateKeyboardEvent.side_effect = ['down', 'up']
        with patch.dict('sys.modules', Quartz=quartz, AppKit=appkit):
            Pointer.__new__(Pointer).escape()
        self.assertEqual([c.args for c in quartz.CGEventPostToPid.call_args_list], [(123, 'down'), (123, 'up')])
        quartz.CGEventPost.assert_not_called()

    def test_session_sends_escape_and_continues(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = detection(hand())
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = [True, True, False]
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [GestureState(escape_requested=True), GestureState(), GestureState()]
            run_session(camera, tracker, pointer, view, policy)
        pointer.escape.assert_called_once()
        pointer.press.assert_not_called()
        self.assertEqual(camera.read.call_count, 3)
        self.assertLess(pointer.method_calls.index(('release', (), {})), pointer.method_calls.index(('escape', (), {})))
