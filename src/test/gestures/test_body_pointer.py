from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from askai.gestures.controller import GestureController
from askai.gestures.preview import Pointer
from askai.gestures.waist import WaistBoundary
from landmark_fixtures import world_points
from test_boundary import run_frames
from test_gestures import hand


def positioned_hand(y, pinched=False, x=.5):
    return [(px + x - .5, py + y - .3) for px, py in hand(pinched)]


class BodyPointerTests(unittest.TestCase):
    def test_full_screen_is_reachable_above_different_hip_heights(self):
        for height in (.4, .6, .7, .9):
            waist = WaistBoundary((0., height), (1., height), None)
            for fraction, expected_y in ((.25, 0.), (.5, .5), (.75, 1.), (.9, 1.)):
                for x, expected_x in ((.25, 0.), (.5, .5), (.75, 1.)):
                    with self.subTest(height=height, fraction=fraction, x=x):
                        points = positioned_hand(height * fraction, x=x)
                        self.assertTrue(waist.allows(points))
                        _, _, states = run_frames([(0., points, waist)])
                        self.assertAlmostEqual(states[0].pointer[0], expected_x)
                        self.assertAlmostEqual(states[0].pointer[1], expected_y)

    def test_lowering_hand_settles_at_exact_bottom_before_hip_boundary(self):
        for height in (.4, .6, .7, .9):
            with self.subTest(height=height):
                waist = WaistBoundary((0., height), (1., height), None)
                samples = [(0., positioned_hand(height * .5), waist)]
                samples += [(i * .02, positioned_hand(height * .75), waist) for i in range(1, 151)]
                _, _, states = run_frames(samples)
                self.assertEqual(states[-1].pointer[1], 1.)

    def test_bottom_click_has_room_for_fingers_to_lower_without_releasing(self):
        for height in (.4, .6, .7, .9):
            with self.subTest(height=height):
                waist = WaistBoundary((0., height), (1., height), None)
                opened = positioned_hand(height * .75)
                closed = positioned_hand(height * .85, True)
                self.assertTrue(waist.allows(closed))
                pointer, notify, states = run_frames([(0., opened, waist), (.1, closed, waist),
                                                      (.2, closed, waist), (.3, opened, waist)])
                self.assertEqual(states[0].pointer, (.5, 1.))
                self.assertTrue(states[1].dragging)
                self.assertTrue(states[2].dragging)
                self.assertFalse(states[3].dragging)
                self.assertTrue(all(state.pointer == (.5, 1.) for state in states))
                self.assertEqual([c.args[0] for c in notify.call_args_list], ['pinch', 'release'])
                pointer.press.assert_called()

    def test_hip_detection_jitter_does_not_move_a_held_drag(self):
        waist = WaistBoundary((0., .6), (1., .6), None)
        samples = [(0., positioned_hand(.4), waist), (.1, positioned_hand(.4, True), waist)]
        samples += [(time, positioned_hand(.4, True), WaistBoundary((0., height), (1., height), None))
                    for time, height in ((.3, .63), (.7, .57), (.8, .64), (1., .58))]
        _, notify, states = run_frames(samples)
        self.assertTrue(all(state.pointer == states[0].pointer for state in states))
        self.assertTrue(all(state.dragging for state in states[1:]))
        notify.assert_called_once_with('pinch')

    def test_drag_can_move_up_from_bottom_and_return_to_bottom(self):
        waist = WaistBoundary((0., .6), (1., .6), None)
        samples = [(0., positioned_hand(.45), waist), (.1, positioned_hand(.45, True), waist),
                   (.59, positioned_hand(.45, True), waist), (.6, positioned_hand(.36, True), waist)]
        samples += [(1. + i * .02, positioned_hand(.45, True), waist) for i in range(151)]
        _, _, states = run_frames(samples)
        self.assertLess(states[3].pointer[1], 1.)
        self.assertEqual(states[-1].pointer[1], 1.)
        self.assertTrue(all(state.dragging for state in states[1:]))

    def test_sloped_hip_line_is_mirrored_with_the_hand_mapping(self):
        waist = WaistBoundary((0., .5), (1., .7), None)
        for x in (.25, .5, .75):
            height = waist.mirrored().height_at(x)
            points = positioned_hand(.75 * height, x=x)
            _, _, states = run_frames([(0., points, waist)])
            self.assertAlmostEqual(states[0].pointer[1], 1.)

    def test_mapping_does_not_bypass_block_below_hips_or_without_body(self):
        waist = WaistBoundary((0., .6), (1., .6), None)
        pointer, notify, states = run_frames([(0., positioned_hand(.45), waist),
            (.1, positioned_hand(.61, True), waist), (.2, positioned_hand(.45, True), None)])
        pointer.press.assert_not_called()
        self.assertIsNone(states[1].pointer)
        self.assertIsNone(states[2].pointer)

    def test_bottom_target_maps_to_native_monitor_bounds_at_different_resolutions(self):
        layouts = [[(0, 0, 1920, 1080)], [(0, 0, 3840, 2160)],
                   [(-1920, 0, 1920, 1080), (0, 0, 2560, 1440)]]
        waist = WaistBoundary((0., .6), (1., .6), None)
        _, _, states = run_frames([(0., positioned_hand(.45, x=.75), waist)])
        for layout in layouts:
            with self.subTest(layout=layout):
                pointer = Pointer.__new__(Pointer)
                pointer._screens = [NS(origin=NS(x=x, y=y), size=NS(width=w, height=h)) for x, y, w, h in layout]
                pointer._position = None
                pointer._pressed = False
                pointer._mouse = Mock()
                quartz = Mock()
                with patch.dict('sys.modules', Quartz=quartz):
                    pointer.move(*states[0].pointer)
                    pointer.press()
                x, y, width, height = layout[-1]
                self.assertEqual(pointer._position, (x + width - 2, y + height - 2))
                pointer._mouse.mouseDown.assert_called_once_with(_pause=False)

    def test_invalid_extrapolated_boundary_does_not_create_pointer_target(self):
        control = GestureController()
        points = positioned_hand(.3)
        for height in (0., float('nan')):
            waist = WaistBoundary((0., height), (1., height), None)
            state = control.update(points, world_points=world_points(points), waist=waist)
            self.assertIsNone(state.pointer)
