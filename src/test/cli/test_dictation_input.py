import unittest
from unittest.mock import patch
from askai.cli.dictation_input import cancel_requested, capture_cancellation, Keyboard


class DictationInputTests(unittest.TestCase):
    def test_ui_cancellation_never_reads_terminal_and_is_restored_on_failure(self):
        from threading import Event
        cancelled = Event()
        with patch('askai.cli.dictation_input.sys.stdin') as stdin, \
                patch.object(Keyboard, 'wait_keystroke') as read:
            stdin.isatty.return_value = True
            with self.assertRaises(RuntimeError):
                with capture_cancellation(cancelled.is_set):
                    self.assertFalse(cancel_requested())
                    cancelled.set()
                    self.assertTrue(cancel_requested())
                    read.assert_not_called()
                    raise RuntimeError('capture failed')
            read.return_value = Keyboard.VK_ESC
            self.assertTrue(cancel_requested())
            read.assert_called_once()

    def test_only_escape_cancels_and_input_is_nonblocking(self):
        with patch('askai.cli.dictation_input.sys.stdin') as stdin, \
                patch.object(Keyboard, 'wait_keystroke') as read:
            stdin.isatty.return_value = True
            for key in (Keyboard.VK_ESC, Keyboard.VK_ENTER, None):
                read.return_value = key
                self.assertEqual(cancel_requested(), key == Keyboard.VK_ESC)
                read.assert_called_with(blocking=False, ignore_error_keys=True)

    def test_non_terminal_does_not_read_keyboard(self):
        with patch('askai.cli.dictation_input.sys.stdin') as stdin, \
                patch.object(Keyboard, 'wait_keystroke') as read:
            stdin.isatty.return_value = False
            self.assertFalse(cancel_requested())
            read.assert_not_called()
