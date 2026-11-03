from landmark_fixtures import POINTER_WAIST, detection, world_points
from test_gestures import hand
import unittest
from unittest.mock import Mock, patch
import numpy as np
from askai.gestures.controller import GestureController, GestureState
from askai.gestures.scroll import ScrollMotion, is_scroll_hand
from askai.gestures.session import run_session, authorize
from askai.core.permissions.grants import GrantPolicy, GrantDenied


def fingers():
    points = [(.5, .9)] * 21
    points[3], points[4] = (.3, .6), (.4, .8)
    for base, x in ((5, .35), (9, .45), (13, .55), (17, .65)):
        points[base:base+4] = [(x, .65), (x, .5), (x, .4), (x, .2 if base < 13 else .75)]
    return points


def update(control, points):
    return control.update(points, waist=POINTER_WAIST, world_points=world_points(points))


class ScrollTests(unittest.TestCase):
    def test_repeated_detection_flicker_keeps_one_mode_and_blocks_other_gestures(self):
        from test_boundary import run_frames, WAIST
        raised = [(x, y - .55) for x, y in fingers()]
        samples = [(0., raised, WAIST), (.11, raised, WAIST)]
        for index in range(1, 11):
            samples.extend([(index * .2, hand() if index % 2 else [], WAIST),
                            (index * .2 + .1, raised, WAIST)])
        samples.extend([(3., hand(), WAIST), (3.499, hand(), WAIST), (3.5, hand(), WAIST)])
        pointer, notify, states = run_frames(samples)
        events = [entry.args[0] for entry in notify.call_args_list]
        self.assertEqual(events, ['scroll_start', 'scroll_up', 'scroll_stop'])
        self.assertTrue(all(state.scrolling for state in states[:-1]))
        for state in states[2:-3:2]:
            self.assertEqual(state, GestureState(scrolling=True))
        pointer.move.assert_called_once()
        pointer.press.assert_not_called()
        pointer.double_click.assert_not_called()

    def test_brief_body_loss_does_not_restart_mode_or_repeat_boundary_command(self):
        from test_boundary import run_frames, WAIST
        points = fingers()
        pointer, notify, states = run_frames([(0., points, WAIST), (.1, points, WAIST),
                                             (.2, points, None), (.3, points, WAIST),
                                             (.4, points, WAIST)])
        self.assertTrue(all(state.scrolling for state in states))
        events = [entry.args[0] for entry in notify.call_args_list]
        self.assertEqual(events.count('scroll_start'), 1)
        self.assertNotIn('scroll_stop', events)
        pointer.scroll_boundary.assert_called_once_with('bottom')
        pointer.move.assert_not_called()

    def test_session_scrolls_by_height_and_reaches_boundaries_with_pointer_locked(self):
        from test_boundary import run_frames, WAIST
        samples = [(time, [(x, y + height - .9) for x, y in fingers()], WAIST)
                   for time, height in ((0., .5), (.11, .35), (.22, .3),
                                        (.33, .66), (.44, .2), (.55, .2), (.66, .8))]
        pointer, _, states = run_frames(samples)
        self.assertEqual([c.args[0] for c in pointer.scroll.call_args_list], [4, 6, -4])
        self.assertEqual([c.args[0] for c in pointer.scroll_boundary.call_args_list], ['top', 'bottom'])
        self.assertTrue(all(state.scrolling and state.pointer is None for state in states))
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()

    def test_neutral_height_keeps_scroll_mode_and_all_other_gestures_blocked(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        centered = [(x, y - .4) for x, y in fingers()]
        for time in (0., .499, .5, 1., 10.):
            clock.return_value = time
            self.assertEqual(update(control, centered), GestureState(scrolling=True))

    def test_other_gesture_holds_start_only_after_half_second_without_two_fingers(self):
        from test_thumbs_up import thumbs_up
        from test_rock import rock
        from test_phone import phone
        from test_escape import palm
        for pose, progress, requested in ((thumbs_up, 'exit_progress', 'exit_requested'),
                                          (rock, 'abort_progress', 'abort_requested'),
                                          (phone, 'voice_progress', 'voice_requested'),
                                          (palm, 'double_click_progress', 'double_click_requested')):
            with self.subTest(gesture=pose.__name__):
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                self.assertTrue(update(control, fingers()).scrolling)
                for time in (1., 1.499):
                    clock.return_value = time
                    self.assertEqual(update(control, pose()), GestureState(scrolling=True))
                clock.return_value = 1.5
                state = update(control, pose())
                self.assertEqual(getattr(state, progress), 0.)
                self.assertFalse(getattr(state, requested))
                clock.return_value = 1.999
                self.assertFalse(getattr(update(control, pose()), requested))
                clock.return_value = 2.
                self.assertTrue(getattr(update(control, pose()), requested))

    def test_missing_or_invalid_hand_stops_scroll_without_extending_resume_delay(self):
        for absent in ([], [(float('nan'), .5)] * 21):
            clock = Mock(return_value=0.)
            control = GestureController(clock)
            update(control, fingers())
            for time in (1., 1.499):
                clock.return_value = time
                self.assertEqual(update(control, absent), GestureState(scrolling=True))
                self.assertEqual(update(control, hand()), GestureState(scrolling=True))
            clock.return_value = 1.5
            self.assertIsNotNone(update(control, hand()).pointer)

    def test_height_controls_continuous_scroll_and_edges(self):
        clock = Mock(return_value=0.)
        motion = ScrollMotion(clock)
        self.assertEqual(motion.update(.5), 0)
        clock.return_value = .2
        self.assertGreater(motion.update(.35), 0)
        clock.return_value = .4
        self.assertGreater(motion.update(.35), 0)
        clock.return_value = .6
        self.assertLess(motion.update(.65), 0)
        clock.return_value = .8
        self.assertEqual(motion.update(.5), 0)
        motion.update(.2)
        self.assertEqual(motion.boundary, 'top')
        motion.update(.2)
        self.assertIsNone(motion.boundary)
        motion.update(.8)
        self.assertEqual(motion.boundary, 'bottom')

    def test_returning_two_fingers_keeps_mode_and_next_release_restarts_delay(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        update(control, fingers())
        clock.return_value = 1.
        self.assertEqual(update(control, hand()), GestureState(scrolling=True))
        clock.return_value = 1.2
        state = update(control, [(x, y - .4) for x, y in fingers()])
        self.assertEqual(state, GestureState(scrolling=True))
        clock.return_value = 2.
        self.assertEqual(update(control, hand()), GestureState(scrolling=True))
        clock.return_value = 2.499
        self.assertEqual(update(control, hand()), GestureState(scrolling=True))
        clock.return_value = 2.5
        self.assertIsNotNone(update(control, hand()).pointer)

    def test_scroll_mode_and_release_delay_do_not_evaluate_other_gestures(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        with patch('askai.gestures.controller.is_thumbs_up') as thumb, patch(
                'askai.gestures.controller.is_open_palm') as palm, patch(
                'askai.gestures.controller.is_rock_hand') as rock, patch(
                'askai.gestures.controller.is_phone_hand') as phone:
            update(control, fingers())
            clock.return_value = 1.
            self.assertEqual(update(control, hand(True)), GestureState(scrolling=True))
            clock.return_value = 1.499
            self.assertEqual(update(control, hand(True)), GestureState(scrolling=True))
        for detector in (thumb, palm, rock, phone):
            detector.assert_not_called()
        clock.return_value = 1.5
        self.assertFalse(update(control, hand(True)).dragging)
        update(control, hand())
        self.assertTrue(update(control, hand(True)).dragging)

    def test_only_two_extended_fingers_select_scroll(self):
        self.assertTrue(is_scroll_hand(world_points(fingers())))
        for index, position in ((8, (.35, .75)), (12, (.45, .75)), (16, (.55, .2)),
                                (20, (.65, .2))):
            points = fingers()
            points[index] = position
            self.assertFalse(is_scroll_hand(world_points(points)))

    def test_neutral_zone_and_rate_limit(self):
        clock = Mock(return_value=0.)
        motion = ScrollMotion(clock)
        motion.update(.5)
        for y in (.51, .49, .505, .495):
            clock.return_value += .2
            self.assertEqual(motion.update(y), 0)
        clock.return_value += .2
        self.assertGreater(motion.update(.3), 0)
        self.assertEqual(motion.update(.3), 0)

    def test_controller_freezes_pointer_and_disallows_clicks(self):
        control = GestureController()
        state = update(control, fingers())
        self.assertTrue(state.scrolling)
        moved = [(x, y - .06) for x, y in fingers()]
        state = update(control, moved)
        self.assertEqual(state.scroll_steps, 0)
        self.assertIsNone(state.pointer)
        self.assertFalse(state.dragging)
        update(control, [])
        self.assertEqual(update(control, moved).scroll_steps, 0)

    def test_scroll_denial_prevents_start(self):
        policy = GrantPolicy(lambda key: 'deny' if key.endswith('desktop.pointer.scroll') else 'allow')
        with self.assertRaises(GrantDenied):
            authorize(policy, Mock())

    def test_session_emits_direction_changes_not_every_frame(self):
        camera, tracker, pointer, view, policy, notify = [Mock() for _ in range(6)]
        camera.read.return_value = True, np.zeros((10, 10, 3))
        tracker.detect.return_value = detection(hand())
        view.prepare.side_effect = lambda frame: frame
        view.update.side_effect = [True] * 5 + [False]
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = [GestureState(scrolling=True, scroll_steps=n)
                for n in (0, 1, 2, -1)] + [GestureState(), GestureState()]
            run_session(camera, tracker, pointer, view, policy, notify=notify)
        self.assertEqual([c.args[0] for c in notify.call_args_list],
                         ['scroll_start', 'scroll_up', 'scroll_down', 'scroll_stop'])
        self.assertEqual([c.args[0] for c in pointer.scroll.call_args_list], [1, 2, -1])
        pointer.move.assert_not_called()
        pointer.press.assert_not_called()

    def test_session_blocks_pointer_targets_until_scroll_gesture_ends(self):
        camera, tracker, pointer, view, policy = [Mock() for _ in range(5)]
        camera.read.return_value = True, np.zeros((100, 100, 3))
        tracker.detect.return_value = detection(hand())
        view.prepare.side_effect = lambda frame: frame
        view.update.return_value = True
        states = [GestureState(pointer=(.2, .3), scrolling=True, scroll_steps=1),
                  GestureState(pointer=(.6, .8), scrolling=True, scroll_steps=0),
                  GestureState(pointer=(.8, .9), scrolling=True, scroll_steps=-1),
                  GestureState(pointer=(.4, .5))]
        with patch('askai.gestures.session.GestureController') as controller:
            controller.return_value.update.side_effect = states
            run_session(camera, tracker, pointer, view, policy,
                        should_stop=Mock(side_effect=[False] * len(states) + [True]))
        pointer.move.assert_called_once_with(.4, .5)
        self.assertEqual([entry.args[0] for entry in pointer.scroll.call_args_list], [1, -1])
