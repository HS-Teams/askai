import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from askai.gestures.preview import Pointer
from askai.gestures import sfx


class SoundTests(unittest.TestCase):
    def test_abort_sound_follows_request_cancellation(self):
        import ast
        from pathlib import Path
        from askai.gestures import command
        source = Path(command.__file__)
        node = next(node for node in ast.walk(ast.parse(source.read_text()))
                    if isinstance(node, ast.FunctionDef) and node.name == 'notify')
        abort = Mock()
        scope = dict(MESSAGES=command.MESSAGES, events=Mock(), AIReply=Mock(),
                     abort_current_request=abort, play_abort=sfx.play_abort)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
        with patch.object(sfx, '_play') as sound:
            sound.side_effect = lambda filename: abort.assert_called_once_with()
            scope['notify']('abort')
        sound.assert_called_once_with('gesture-stop.mp3')

    def test_requested_assets_exist_and_are_routed(self):
        self.assertEqual(sfx.SFX_DIR.parts[-2:], ('sfx', 'gestures'))
        for name, filename in (
            ('click', 'gesture-click.ogg'), ('drag', 'gesture-move.mp3'),
            ('double_click', 'gesture-double-click.mp3'),
            ('grab', 'gesture-grab.mp3'),
            ('scroll_up', 'gesture-slide-up.mp3'), ('scroll_down', 'gesture-slide-down.mp3'),
            ('abort', 'gesture-stop.mp3'), ('quit', 'gesture-quit.mp3'),
            ('ptt', 'gesture-ptt.mp3'), ('init', 'gesture-init.mp3'),
        ):
            with self.subTest(name=name), patch.object(sfx, '_play') as play:
                getattr(sfx, 'play_' + name)()
                play.assert_called_once_with(filename)
                self.assertTrue((sfx.SFX_DIR / filename).is_file())

    def test_every_scroll_direction_notification_plays_its_sound(self):
        import ast
        from askai.gestures import command
        from pathlib import Path

        source = Path(command.__file__)
        node = next(node for node in ast.walk(ast.parse(source.read_text()))
                    if isinstance(node, ast.FunctionDef) and node.name == 'notify')
        scope = dict(MESSAGES=command.MESSAGES, events=Mock(), AIReply=Mock(),
                     play_scroll_up=sfx.play_scroll_up, play_scroll_down=sfx.play_scroll_down)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
        with patch.object(sfx, '_play') as play:
            for event in ('scroll_start', 'scroll_up', 'scroll_down', 'scroll_up', 'scroll_down', 'scroll_stop'):
                scope['notify'](event)
        self.assertEqual([call.args[0] for call in play.call_args_list],
                         ['gesture-slide-up.mp3', 'gesture-slide-down.mp3'] * 2)

    def test_click_and_drag_sounds_are_exclusive_and_do_not_repeat(self):
        for drag in (False, True):
            with self.subTest(drag=drag), patch.dict('sys.modules', Quartz=Mock()), patch.object(
                    sfx, 'play_click') as click, patch.object(sfx, 'play_drag') as move:
                pointer = Pointer.__new__(Pointer)
                pointer._mouse = Mock()
                pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=100, height=100))]
                pointer._position = (49.5, 49.5)
                pointer._pressed = False
                pointer.press()
                pointer.press()
                if drag:
                    pointer.move(.7, .5)
                    pointer.move(.8, .5)
                pointer.release()
                pointer.release()
                self.assertEqual(click.call_count, int(not drag))
                self.assertEqual(move.call_count, int(drag))

    def test_move_sound_starts_at_twenty_pixels_once_per_drag(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=1001, height=1001))]
        pointer._position = (500., 500.)
        pointer._pressed = False
        with patch.dict('sys.modules', Quartz=Mock()), patch.object(sfx, 'play_drag') as sound, patch.object(sfx, 'play_click'):
            pointer.press()
            for x in (.505, .510, .519, .5199):
                pointer.move(x, .5)
            sound.assert_not_called()
            pointer.move(.520, .5)
            sound.assert_called_once_with()
            pointer.move(.540, .5)
            pointer.move(.500, .5)
            sound.assert_called_once_with()
            pointer.release()
            pointer.press()
            pointer.move(.519, .5)
            sound.assert_called_once_with()
            pointer.move(.520, .5)
            self.assertEqual(sound.call_count, 2)

    def test_move_sound_uses_straight_line_distance_including_diagonals(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=1001, height=1001))]
        pointer._position = (500., 500.)
        pointer._pressed = False
        with patch.dict('sys.modules', Quartz=Mock()), patch.object(sfx, 'play_drag') as sound:
            pointer.press()
            # Repeated small movements must not accumulate into an early sound.
            for x in (.51, .49, .51, .49):
                pointer.move(x, .5)
            sound.assert_not_called()
            pointer.move(.512, .516)  # sqrt(12**2 + 16**2) == 20
            sound.assert_called_once_with()

    def test_unknown_initial_position_does_not_play_move_sound_immediately(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=1001, height=1001))]
        pointer._position = None
        pointer._pressed = False
        with patch.dict('sys.modules', Quartz=Mock()), patch.object(sfx, 'play_drag') as sound:
            pointer.press()
            pointer.move(.5, .5)
            pointer.move(.519, .5)
            sound.assert_not_called()
            pointer.move(.52, .5)
            sound.assert_called_once_with()

    def test_grab_sound_fires_once_only_after_one_second_without_movement(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._position = (500., 500.)
        pointer._pressed = False
        with patch('askai.gestures.preview.monotonic', return_value=0.) as clock, patch.object(sfx, 'play_grab') as sound:
            pointer.press()
            for time in (.5, .999, 1.):
                clock.return_value = time
                pointer.press()
                sound.assert_not_called()
            clock.return_value = 1.001
            pointer.press()
            sound.assert_called_once_with()
            clock.return_value = 10.
            pointer.press()
            sound.assert_called_once_with()
        pointer._mouse.mouseDown.assert_called_once_with(_pause=False)

    def test_releasing_pinch_cancels_grab_and_next_press_restarts_timer(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._position = (500., 500.)
        pointer._pressed = False
        with patch.dict('sys.modules', Quartz=Mock()), patch.object(sfx, 'play_click'), patch.object(
                sfx, 'play_grab') as sound, patch('askai.gestures.preview.monotonic', return_value=0.) as clock:
            pointer.press()
            clock.return_value = .9
            pointer.release()
            clock.return_value = 10.
            pointer.press()
            clock.return_value = 11.
            pointer.press()
            sound.assert_not_called()
            clock.return_value = 11.001
            pointer.press()
            sound.assert_called_once_with()
            pointer.release()
            pointer.press()
            clock.return_value = 12.002
            pointer.press()
            self.assertEqual(sound.call_count, 2)

    def test_move_sound_and_grab_sound_have_independent_thresholds(self):
        pointer = Pointer.__new__(Pointer)
        pointer._mouse = Mock()
        pointer._screens = [NS(origin=NS(x=0, y=0), size=NS(width=1001, height=1001))]
        pointer._position = (500., 500.)
        pointer._pressed = False
        with patch.dict('sys.modules', Quartz=Mock()), patch.object(sfx, 'play_drag') as move, patch.object(
                sfx, 'play_grab') as grab, patch('askai.gestures.preview.monotonic', return_value=0.) as clock:
            pointer.press()
            clock.return_value = .7
            pointer.move(.52, .5)
            pointer.press()
            move.assert_called_once_with()
            grab.assert_not_called()
            clock.return_value = 1.001
            pointer.press()
            grab.assert_called_once_with()
            move.assert_called_once_with()
