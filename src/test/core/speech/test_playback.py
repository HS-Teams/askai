from pathlib import Path
from threading import Event
import subprocess
import unittest
from unittest.mock import Mock, patch
from askai.core.speech.playback import play_speech


class PlaybackTests(unittest.TestCase):
    def test_cancel_terminates_only_owned_player(self):
        process = Mock()
        process.__enter__ = Mock(return_value=process)
        process.__exit__ = Mock()
        process.poll.side_effect = [None, 0]
        cancel = Mock()
        cancel.is_set.return_value = False
        cancel.wait.return_value = True
        with patch('askai.core.speech.playback.subprocess.Popen', return_value=process) as popen:
            play_speech(Path('/tmp/a song.wav'), 1, cancel)
        self.assertEqual(popen.call_args.args[0][-1], '/tmp/a song.wav')
        self.assertNotIn('shell', popen.call_args.kwargs)
        process.terminate.assert_called_once()
        process.kill.assert_not_called()

    def test_cancel_escalates_if_player_ignores_termination(self):
        process = Mock()
        process.__enter__ = Mock(return_value=process)
        process.__exit__ = Mock()
        process.poll.side_effect = [None, -9]
        process.wait.side_effect = [subprocess.TimeoutExpired('ffplay', 2), -9]
        cancel = Mock()
        cancel.is_set.return_value = False
        cancel.wait.return_value = True
        with patch('askai.core.speech.playback.subprocess.Popen', return_value=process):
            play_speech(Path('/tmp/song.wav'), 1, cancel)
        process.kill.assert_called_once()

    def test_cancel_before_start_never_launches_player(self):
        cancelled = Event()
        cancelled.set()
        with patch('askai.core.speech.playback.subprocess.Popen') as popen:
            play_speech(Path('/tmp/song.wav'), 1, cancelled)
        popen.assert_not_called()

    def test_text_presentation_starts_only_after_player_started(self):
        import tempfile
        import wave
        from askai.core.speech.playback import synchronized_speech
        from threading import Event
        started_playing, text_done = Event(), Event()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'voice.wav'
            with wave.open(str(path), 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(1000)
                wav.writeframes(b'\0\0' * 1000)
            def play(path, tempo, cancelled, started, timing):
                started_playing.set()
                started.set()
                self.assertTrue(text_done.wait(2))
            def present(duration, cancelled):
                self.assertTrue(started_playing.is_set())
                self.assertEqual(duration.duration, .5)
                text_done.set()
            with patch('askai.core.speech.playback.play_speech', side_effect=play):
                synchronized_speech(path, 2, Event(), present)

    def test_ffplay_clock_ignores_diagnostics_and_nan(self):
        from io import BytesIO
        from askai.core.speech.playback import _read_position
        from askai.core.speech.timing import PlaybackTiming
        timing = PlaybackTiming(3)
        _read_position(BytesIO(b'warning\n nan M-A: 0\r  1.25 M-A: 0.0\r'), timing)
        self.assertEqual(timing.position, 1.25)
