import unittest
from unittest.mock import MagicMock, Mock
from askai.cli.gestures_loading import gestures_loading, STAGES


class GestureLoadingTests(unittest.TestCase):
    def test_startup_failure_closes_spinner_and_propagates_error(self):
        console = MagicMock()
        failure = RuntimeError('Camera unavailable')
        with self.assertRaisesRegex(RuntimeError, 'Camera unavailable'):
            with gestures_loading(console, lambda text: text) as update:
                update('camera')
                raise failure
        exit_args = console.status.return_value.__exit__.call_args.args
        self.assertIs(exit_args[0], RuntimeError)
        self.assertIs(exit_args[1], failure)

    def test_spinner_tracks_translated_stage_without_a_progress_bar(self):
        console = Mock()
        status = console.status.return_value.__enter__ = Mock(return_value=Mock())
        console.status.return_value.__exit__ = Mock(return_value=False)
        with gestures_loading(console, lambda text: 'Translated: ' + text) as update:
            for stage in STAGES:
                update(stage)
        self.assertEqual(console.status.call_args.kwargs, {'spinner': 'dots'})
        self.assertEqual(status.return_value.update.call_count, len(STAGES))
        self.assertEqual(status.return_value.update.call_args.args[0].plain,
                         'Translated: Preparing gesture preview...')
