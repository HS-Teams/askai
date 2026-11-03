from landmark_fixtures import POINTER_WAIST
import unittest
from unittest.mock import Mock
from askai.gestures.controller import GestureController
from landmark_fixtures import world_points
from test_gestures import hand
from test_escape import palm
from test_rock import rock


def update(control, points):
    return control.update(points, waist=POINTER_WAIST, world_points=world_points(points))


class CooldownTests(unittest.TestCase):
    def test_pinch_cooldown_starts_at_release_including_long_drag(self):
        for duration in (.25, 5.):
            with self.subTest(duration=duration):
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                update(control, hand())
                self.assertTrue(update(control, hand(True)).dragging)
                clock.return_value = duration
                self.assertTrue(update(control, hand(True)).dragging)
                self.assertFalse(update(control, hand()).dragging)
                clock.return_value = duration + .999
                self.assertFalse(update(control, hand(True)).dragging)
                clock.return_value = duration + 1.
                # A pinch attempted during cooldown must be opened again.
                self.assertFalse(update(control, hand(True)).dragging)
                update(control, hand())
                self.assertTrue(update(control, hand(True)).dragging)

    def test_cooldown_does_not_freeze_pointing_or_block_phone(self):
        from test_phone import phone
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        update(control, hand())
        update(control, hand(True))
        origin = update(control, hand()).pointer
        moved = [(x + .1, y) for x, y in hand()]
        self.assertGreater(update(control, moved).pointer[0], origin[0])
        update(control, phone())
        clock.return_value = .5
        self.assertTrue(update(control, phone()).voice_requested)

    def test_pinch_cooldown_survives_loss_boundary_and_command_change(self):
        for interruption in ('lost', 'boundary', 'command'):
            with self.subTest(interruption=interruption):
                clock = Mock(return_value=0.)
                control = GestureController(clock)
                update(control, hand())
                update(control, hand(True))
                clock.return_value = .25
                if interruption == 'lost':
                    update(control, [])
                elif interruption == 'boundary':
                    control.suspend()
                else:
                    update(control, palm())
                update(control, hand())
                clock.return_value = 1.249
                self.assertFalse(update(control, hand(True)).dragging)
                clock.return_value = 1.25
                update(control, hand())
                self.assertTrue(update(control, hand(True)).dragging)

    def test_palm_and_rock_cooldown_survives_reset_and_requires_new_pose(self):
        for pose, field in ((palm, 'double_click_requested'), (rock, 'abort_requested')):
            for interruption in ('open', 'lost', 'boundary'):
                with self.subTest(pose=pose.__name__, interruption=interruption):
                    clock = Mock(return_value=0.)
                    control = GestureController(clock)
                    update(control, pose())
                    clock.return_value = .5
                    self.assertTrue(getattr(update(control, pose()), field))
                    clock.return_value = .75
                    if interruption == 'boundary':
                        control.suspend()
                    else:
                        update(control, hand() if interruption == 'open' else [])
                    self.assertFalse(getattr(update(control, pose()), field))
                    clock.return_value = 1.25  # Full 0.5 s hold, still within cooldown.
                    self.assertFalse(getattr(update(control, pose()), field))
                    clock.return_value = 1.499
                    self.assertFalse(getattr(update(control, pose()), field))
                    clock.return_value = 1.5
                    self.assertTrue(getattr(update(control, pose()), field))
                    clock.return_value = 10.
                    self.assertFalse(getattr(update(control, pose()), field))

    def test_command_cooldowns_are_independent(self):
        clock = Mock(return_value=0.)
        control = GestureController(clock)
        update(control, palm())
        clock.return_value = .5
        self.assertTrue(update(control, palm()).double_click_requested)
        update(control, rock())
        clock.return_value = 1.
        self.assertTrue(update(control, rock()).abort_requested)
