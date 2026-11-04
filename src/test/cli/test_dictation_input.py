import unittest
from unittest.mock import patch
from askai.cli.dictation_input import cancel_requested, Keyboard


class DictationInputTests(unittest.TestCase):
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
