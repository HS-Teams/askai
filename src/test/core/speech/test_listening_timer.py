import unittest
from unittest.mock import Mock
from askai.core.speech.listening_timer import listening_timer


class TimerTests(unittest.TestCase):
    def test_unlimited_capture_shows_elapsed_time(self):
        stopped = Mock()
        stopped.is_set.return_value = False
        stopped.wait.side_effect = [False, False, True]
        render = Mock()
        listening_timer(0, stopped, render)
        self.assertEqual(
            [call.args for call in render.call_args_list],
            [("00:00", False), ("00:01", True), ("00:02", True)],
        )
        stopped.set.assert_not_called()

    def test_configured_limit_counts_down_without_stopping_capture(self):
        stopped = Mock()
        stopped.is_set.return_value = False
        stopped.wait.side_effect = [False, False, True]
        render = Mock()
        listening_timer(2, stopped, render)
        self.assertEqual(
            [call.args[0] for call in render.call_args_list],
            ["00:02", "00:01", "00:00"],
        )
        stopped.set.assert_not_called()

    def test_ten_second_limit_counts_from_ten_to_zero(self):
        stopped = Mock()
        stopped.is_set.return_value = False
        stopped.wait.side_effect = [False] * 10 + [True]
        render = Mock()
        listening_timer(10, stopped, render)
        self.assertEqual(
            [call.args[0] for call in render.call_args_list],
            [f"00:{second:02d}" for second in range(10, -1, -1)],
        )
