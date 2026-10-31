import unittest
from unittest.mock import Mock, patch
from askai.cli.listening_indicator import ListeningIndicator


class ListeningIndicatorTests(unittest.TestCase):
    def test_ticks_update_one_status_and_stop_before_following_output(self):
        with patch("askai.cli.listening_indicator.Status") as factory:
            status = factory.return_value
            translate = Mock(return_value="Ouvindo…")
            console = Mock()
            view = ListeningIndicator(console, translate)
            view.update(True, "Listening… 00:10")
            view.update(True, "Listening… 00:09")
            status.start.assert_called_once()
            rendered = status.update.call_args.args[0]
            self.assertEqual(rendered.plain, "Ouvindo… 00:09")
            self.assertTrue(rendered.no_wrap)
            console.print.assert_not_called()
            view.update(False)
            status.stop.assert_called_once()
            view.update(True, "Listening… 00:10")
            self.assertEqual(status.start.call_count, 2)
            self.assertTrue(
                all(call.args == ("Listening…",) for call in translate.call_args_list)
            )
