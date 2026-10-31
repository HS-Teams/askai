from threading import Event
import unittest
from unittest.mock import Mock, patch
from askai.core.speech.pcm_stream import play_pcm_chunks, StartedSpeechError


class PCMStreamTests(unittest.TestCase):
    def player(self):
        process = Mock(returncode=0)
        process.poll.return_value = 0
        process.stdin.closed = False
        return process

    def test_first_chunk_is_played_before_rest_is_received(self):
        process = self.player()
        def chunks():
            yield b'\x01\x02'
            process.stdin.write.assert_called_once_with(b'\x01\x02')
            process.stdin.flush.assert_called_once()
            yield b'\x03\x04'
        with patch('askai.core.speech.pcm_stream.subprocess.Popen', return_value=process):
            self.assertEqual(play_pcm_chunks(chunks(), 24000, 1, Event()), b'\x01\x02\x03\x04')

    def test_partial_failure_does_not_become_retryable_provider_error(self):
        process = self.player()
        def chunks():
            yield b'\x01\x02'
            raise OSError('connection lost')
        with patch('askai.core.speech.pcm_stream.subprocess.Popen', return_value=process):
            with self.assertRaises(StartedSpeechError):
                play_pcm_chunks(chunks(), 24000, 1, Event())

    def test_cancelled_stream_never_starts_player(self):
        cancelled = Event()
        cancelled.set()
        with patch('askai.core.speech.pcm_stream.subprocess.Popen') as player:
            self.assertIsNone(play_pcm_chunks([b'\x01\x02'], 24000, 1, cancelled))
            player.assert_not_called()

    def test_broken_pipe_during_cleanup_preserves_non_retryable_playback_error(self):
        process = self.player()
        process.stdin.write.side_effect = BrokenPipeError('player exited')
        process.stdin.close.side_effect = BrokenPipeError('cleanup')
        with patch('askai.core.speech.pcm_stream.subprocess.Popen', return_value=process) as spawn:
            with self.assertRaises(StartedSpeechError):
                play_pcm_chunks([b'\x01\x02'], 24000, 1, Event())
        command = spawn.call_args.args[0]
        self.assertIn('-ch_layout', command)
        self.assertNotIn('-ac', command)
