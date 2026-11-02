import unittest
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch
from askai.gestures.preview import Pointer
from askai.gestures import sfx


class SoundTests(unittest.TestCase):
    def test_requested_assets_exist_and_are_routed(self):
        for name, filename in (
            ('click', 'gesture-click.ogg'), ('drag', 'gesture-move.mp3'),
            ('escape', 'gesture-stop.mp3'), ('quit', 'gesture-quit.mp3'),
            ('ptt', 'gesture-ptt.mp3'), ('init', 'gesture-init.mp3'),
        ):
            with self.subTest(name=name), patch.object(sfx, '_play') as play:
                getattr(sfx, 'play_' + name)()
                play.assert_called_once_with(filename)
                self.assertTrue((sfx.SFX_DIR / filename).is_file())

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
