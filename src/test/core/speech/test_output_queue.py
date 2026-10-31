from pathlib import Path
from threading import Event
import unittest
from unittest.mock import Mock
from askai.core.speech.output_queue import SpeechOutputQueue


class SpeechQueueTests(unittest.TestCase):
    def test_submit_does_not_wait_for_synthesis_and_cancellation_skips_stale_audio(self):
        started, release = Event(), Event()
        def synthesize(text):
            started.set()
            self.assertTrue(release.wait(2))
            return Path(text)
        play, error = Mock(), Mock()
        queue = SpeechOutputQueue(synthesize, play, error)
        try:
            queue.submit('old')
            self.assertTrue(started.wait(1))
            queue.submit('pending')
            queue.cancel()
            queue.submit('new')
            release.set()
            queue.wait()
            self.assertEqual([c.args[0] for c in play.call_args_list], [Path('new')])
            error.assert_not_called()
        finally:
            release.set()
            queue.close()

    def test_cancel_signals_active_playback(self):
        playing, stopped = Event(), Event()
        def play(path, cancelled):
            playing.set()
            self.assertTrue(cancelled.wait(2))
            stopped.set()
        queue = SpeechOutputQueue(lambda _: Path('voice.wav'), play, Mock())
        try:
            queue.submit('hello')
            self.assertTrue(playing.wait(1))
            queue.cancel()
            self.assertTrue(stopped.wait(1))
        finally:
            queue.close()

    def test_errors_surface_and_worker_keeps_processing_in_order(self):
        error, play = Mock(), Mock()
        queue = SpeechOutputQueue(Mock(side_effect=[ValueError('failed'), Path('ok')]), play, error)
        queue.submit('first')
        queue.submit('second')
        queue.wait()
        error.assert_called_once()
        self.assertEqual(play.call_args.args[0], Path('ok'))
        queue.close()
        queue.close()
        with self.assertRaises(RuntimeError):
            queue.submit('closed')

    def test_synchronized_presentation_waits_for_audio_and_uses_job_error_handler(self):
        ready = Event()
        def synthesize(text):
            ready.set()
            return Path('voice.wav')
        default_play, error, present = Mock(), Mock(), Mock()
        queue = SpeechOutputQueue(synthesize, default_play, error)
        try:
            queue.submit('hello', lambda path, cancelled: present(ready.is_set(), path))
            queue.wait()
            present.assert_called_once_with(True, Path('voice.wav'))
            default_play.assert_not_called()
        finally:
            queue.close()
