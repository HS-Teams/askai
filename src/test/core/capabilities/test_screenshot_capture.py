from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from threading import Event
import unittest
from unittest.mock import Mock, patch
from askai.core.component.multimedia.screenshot import capture_screenshot


class ScreenshotCaptureTests(unittest.TestCase):
    def modules(self, folder):
        return {
            'pyautogui': Mock(), 'pause': Mock(),
            'askai.core.askai_events': Mock(), 'askai.core.askai_messages': Mock(),
            'askai.core.component.cache_service': Mock(SCREENSHOTS_DIR=folder),
            'askai.core.component.multimedia.audio_player': Mock(),
        }

    def test_original_countdown_sounds_and_jpeg_capture(self):
        with TemporaryDirectory() as folder:
            modules = self.modules(folder)
            screenshot = modules['pyautogui'].screenshot.return_value
            screenshot.convert.return_value.save.side_effect = lambda p: Path(p).write_bytes(b'jpeg')
            order = Mock()
            order.attach_mock(modules['askai.core.component.multimedia.audio_player'].player.play_sfx, 'sfx')
            order.attach_mock(modules['pyautogui'].screenshot, 'capture')
            with patch.dict(sys.modules, modules):
                target = capture_screenshot(Event())
            self.assertEqual(Path(target).parent, Path(folder))
            self.assertEqual(Path(target).suffix, '.jpeg')
            self.assertEqual(Path(target).read_bytes(), b'jpeg')
            sounds = modules['askai.core.component.multimedia.audio_player'].player.play_sfx
            self.assertEqual([c.args[0] for c in sounds.call_args_list], ['click', 'click', 'click', 'camera-shutter'])
            labels = modules['askai.core.askai_messages'].msg.t
            self.assertEqual([c.args[0] for c in labels.call_args_list], ['Screenshot in: 3', 'Screenshot in: 2', 'Screenshot in: 1'])
            self.assertEqual(order.mock_calls[3][0], 'capture')
            screenshot.convert.assert_called_once_with('RGB')
            screenshot.close.assert_called_once()
            screenshot.convert.return_value.close.assert_called_once()

    def test_cancel_during_countdown_does_not_capture(self):
        with TemporaryDirectory() as folder:
            modules = self.modules(folder)
            cancelled = Event()
            modules['pause'].seconds.side_effect = lambda _: cancelled.set()
            with patch.dict(sys.modules, modules):
                self.assertIsNone(capture_screenshot(cancelled))
            modules['pyautogui'].screenshot.assert_not_called()

    def test_failed_save_removes_partial_file_and_does_not_play_shutter(self):
        with TemporaryDirectory() as folder:
            modules = self.modules(folder)
            def fail(path):
                Path(path).write_bytes(b'partial')
                raise OSError('save failed')
            modules['pyautogui'].screenshot.return_value.convert.return_value.save.side_effect = fail
            with patch.dict(sys.modules, modules), self.assertRaises(OSError):
                capture_screenshot(Event())
            self.assertEqual(list(Path(folder).iterdir()), [])
            self.assertNotIn('camera-shutter', [c.args[0] for c in modules['askai.core.component.multimedia.audio_player'].player.play_sfx.call_args_list])
