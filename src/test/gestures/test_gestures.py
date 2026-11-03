from landmark_fixtures import POINTER_WAIST
from landmark_fixtures import detection, world_points
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController
from askai.gestures.session import authorize, run_session
from askai.core.permissions.grants import GrantPolicy, GrantDenied


def hand(pinched=False):
    points = [(0.5, .5)] * 21
    points[5], points[17] = (.4, .5), (.6, .5)
    points[8] = (.5, .3)
    points[4] = (.51, .3) if pinched else (.7, .3)
    return points


class ControllerTests(unittest.TestCase):
    def test_command_classification_cannot_interrupt_pinch_drag(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True)))
        clock.return_value = .5
        points = hand(True)
        points[8], points[4] = (.7, .3), (.71, .3)
        with patch('askai.gestures.controller.is_thumbs_up', return_value=True), patch(
                'askai.gestures.controller.is_open_palm', return_value=True):
            state = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertTrue(state.dragging)
        self.assertIsNone(state.exit_progress)
        self.assertIsNone(state.abort_progress)
        self.assertGreater(state.pointer[0], .5)


    def test_drag_waits_half_second_but_button_stays_pressed(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        origin = control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        self.assertTrue(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging)
        points = hand(True)
        points[8], points[4] = (.6, .3), (.61, .3)
        clock.return_value = .499
        pending = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertTrue(pending.dragging)
        self.assertEqual(pending.pointer, origin)
        points[8], points[4] = (.7, .3), (.71, .3)
        clock.return_value = .5
        self.assertGreater(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).pointer[0], origin[0])


    def test_pinch_presses_at_target_then_moves_and_releases(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        target = control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        points = hand(True)
        points[8], points[4] = (.65, .3), (.66, .3)
        pressed = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertTrue(pressed.dragging)
        self.assertEqual(pressed.pointer, target)
        for _ in range(100):
            self.assertTrue(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).dragging)
        clock.return_value = .5
        points[8], points[4] = (.75, .3), (.76, .3)
        moved = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertAlmostEqual(moved.pointer[0], target[0] + (.1 / .5) * control.SMOOTHING)
        points[4] = (.95, .3)
        released = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertFalse(released.dragging)
        self.assertEqual(released.pointer, moved.pointer)

    def test_partial_pinch_does_not_freeze_normal_movement(self):
        control = GestureController()
        first = control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        points = hand()
        points[8], points[4] = (.7, .3), (.78, .3)
        state = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertGreater(state.pointer[0], first[0])
        self.assertFalse(state.dragging)

    def test_pinch_drags_and_open_releases(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        for _ in range(3):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        for _ in range(3):
            state = control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True)))
        self.assertTrue(state.dragging)
        points = hand(True)
        points[8], points[4] = (.7, .3), (.71, .3)
        clock.return_value = .5
        moved = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertGreater(moved.pointer[0], state.pointer[0])
        self.assertTrue(moved.dragging)
        self.assertFalse(control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).dragging)
        self.assertFalse(control.update([], waist=POINTER_WAIST, world_points=world_points([])).dragging)

    def test_cancelled_pinch_releases_without_click(self):
        control = GestureController()
        for _ in range(5):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        points = hand()
        points[8], points[4] = (.7, .3), (.775, .3)
        self.assertFalse(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).dragging)
        points[4] = (.9, .3)
        self.assertFalse(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).dragging)

    def test_hand_loss_clears_pointer_hold(self):
        control = GestureController()
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True)))
        control.update([], waist=POINTER_WAIST, world_points=world_points([]))
        points = hand()
        points[8], points[4] = (.2, .3), (.4, .3)
        state = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertAlmostEqual(state.pointer[0], 0.)
        self.assertAlmostEqual(state.pointer[1], .05 / .5)

    def test_one_click_per_stable_pinch_requires_open_hand(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        for _ in range(5):
            self.assertFalse(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging)
        for _ in range(5):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        results = [control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging for _ in range(10)]
        self.assertEqual(results, [True] * 10)
        for _ in range(5):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        clock.return_value = 1.
        self.assertEqual(sum(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging for _ in range(5)), 5)

    def test_missing_hand_disarms_clicks(self):
        control = GestureController()
        for _ in range(5):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        self.assertIsNone(control.update([], waist=POINTER_WAIST, world_points=world_points([])).pointer)
        self.assertFalse(any(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging for _ in range(4)))

    def test_pointer_is_smoothed_and_clamped(self):
        control = GestureController()
        first = control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        points = hand()
        points[8] = (2., -1.)
        second = control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).pointer
        self.assertGreater(second[0], first[0])
        self.assertLess(second[0], 1)
        self.assertTrue(all(0 <= v <= 1 for v in second))

    def test_small_tremors_do_not_move_pointer(self):
        control = GestureController()
        first = control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).pointer
        for offset in (.002, -.002, .003, -.003):
            points = hand()
            points[8] = (.5 + offset, .3)
            self.assertEqual(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).pointer, first)

    def test_camera_margin_maps_to_screen_edges(self):
        for position, expected in (((.25, .25), (0., 0.)), ((.75, .75), (1., 1.)),
                                   ((.5, .5), (.5, .5)), ((0., 1.), (0., 1.))):
            points = hand()
            points[8] = position
            result = GestureController().update(points, waist=POINTER_WAIST, world_points=world_points(points)).pointer
            for actual, wanted in zip(result, expected):
                self.assertAlmostEqual(actual, wanted)

    def test_moving_down_reaches_dock_edge_despite_smoothing(self):
        control = GestureController()
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        points = hand()
        points[8] = (.5, .75)
        for _ in range(100):
            state = control.update(points, waist=POINTER_WAIST, world_points=world_points(points))
        self.assertEqual(state.pointer[1], 1.)


    def test_pinch_release_starts_one_second_cooldown(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        self.assertTrue(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging)
        self.assertFalse(control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand())).dragging)
        clock.return_value = .999
        self.assertFalse(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging)
        clock.return_value = 1.
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        self.assertTrue(control.update(hand(True), waist=POINTER_WAIST, world_points=world_points(hand(True))).dragging)

    def test_relaxed_pinch_presses_without_fingertips_touching(self):
        control = GestureController()
        control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        points = hand()
        points[4] = (.56, .3)
        self.assertTrue(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).dragging)

    def test_loose_pinch_does_not_click(self):
        control = GestureController()
        for _ in range(5):
            control.update(hand(), waist=POINTER_WAIST, world_points=world_points(hand()))
        points = hand()
        points[4] = (.58, .3)
        self.assertFalse(any(control.update(points, waist=POINTER_WAIST, world_points=world_points(points)).dragging for _ in range(15)))


class SessionTests(unittest.TestCase):
    def test_denial_prevents_authorization(self):
        interact = Mock()
        with self.assertRaises(GrantDenied):
            authorize(GrantPolicy(lambda key: 'deny'), interact)
        interact.assert_not_called()

    def test_ask_and_allow(self):
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        self.assertTrue(authorize(GrantPolicy(lambda key: 'ask'), interact))
        interact.assert_called_once()
        self.assertTrue(authorize(GrantPolicy(lambda key: 'allow'), Mock()))

    def test_escape_before_mouse_action_closes_every_resource(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        view.prepare.side_effect = lambda frame: frame
        tracker.detect.return_value = detection(hand())
        view.update.return_value = False
        run_session(camera, tracker, pointer, view, policy)
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()

    def test_camera_failure_closes_resources_without_mouse_actions(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = False, None
        with self.assertRaises(RuntimeError):
            run_session(camera, tracker, pointer, view, policy)
        pointer.move.assert_not_called()
        camera.release.assert_called_once()
        tracker.close.assert_called_once()
        view.close.assert_called_once()

    def test_revocation_stops_before_moving(self):
        camera, tracker, pointer, view = [Mock() for _ in range(4)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        view.prepare.side_effect = lambda frame: frame
        tracker.detect.return_value = detection(hand())
        view.update.return_value = True
        with self.assertRaises(GrantDenied):
            run_session(camera, tracker, pointer, view, GrantPolicy(lambda key: 'deny'))
        pointer.move.assert_not_called()
        camera.release.assert_called_once()
