import io
import unittest
import wave
from unittest.mock import Mock
from speech_recognition import Recognizer, AudioFile
from askai.core.speech.capture import capture_phrase


class CaptureTests(unittest.TestCase):
    def test_long_phrase_and_natural_pause_preserve_final_speech(self):
        sample_rate = 16000
        speech = b'\x10\x27' * sample_rate
        silence = b'\x00\x00' * sample_rate
        data = speech * 11 + silence + speech * 2 + silence * 2
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(data)
        buffer.seek(0)
        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        with AudioFile(buffer) as source:
            result = capture_phrase(recognizer, source, timeout=2, end_silence=1.5)
        self.assertGreater(len(result.frame_data) / 2 / sample_rate, 14)
        self.assertIn(speech, result.frame_data[12 * sample_rate * 2:])

    def test_explicit_limit_is_respected(self):
        recognizer = Mock(non_speaking_duration=0.5)
        source = object()
        capture_phrase(recognizer, source, timeout=2, end_silence=1.5, phrase_limit=30)
        recognizer.listen.assert_called_once_with(source, timeout=2, phrase_time_limit=30)

    def test_invalid_endpoint_configuration_is_rejected(self):
        for silence, limit in ((0, 0), (1.5, -1)):
            with self.assertRaises(ValueError):
                capture_phrase(Mock(), Mock(), timeout=2, end_silence=silence, phrase_limit=limit)

    def capture_samples(self, data):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(data)
        buffer.seek(0)
        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        with AudioFile(buffer) as source:
            return capture_phrase(recognizer, source, timeout=2, end_silence=1.5,
                                  phrase_limit=10, tail_margin=1.5)

    def test_short_phrase_finishes_before_countdown(self):
        speech = b'\x10\x27' * 16000
        silence = b'\x00\x00' * 16000
        audio = self.capture_samples(speech * 2 + silence * 12)
        self.assertLess(len(audio.frame_data) / 32000, 4)

    def test_last_word_crossing_ten_seconds_is_preserved(self):
        speech = b'\x10\x27' * 16000
        last_word = b'\x20\x20' * 16000
        silence = b'\x00\x00' * 16000
        audio = self.capture_samples(speech * 10 + last_word + silence * 3)
        self.assertIn(last_word, audio.frame_data)
        self.assertLess(len(audio.frame_data) / 32000, 12)

    def test_margin_does_not_turn_unlimited_mode_into_a_limit(self):
        recognizer = Mock(non_speaking_duration=0.5)
        capture_phrase(recognizer, None, timeout=2, end_silence=1.5, tail_margin=1.5)
        self.assertIsNone(recognizer.listen.call_args.kwargs['phrase_time_limit'])

    def test_dictation_preserves_short_pause_and_stops_after_three_seconds(self):
        from askai.core.speech.dictation import END_SILENCE_SECONDS

        rate = 16000
        speech = b'\x10\x27' * rate
        last_words = b'\x20\x20' * rate
        silence = b'\x00\x00' * rate
        after_stop = b'\x30\x30' * rate
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(rate)
            wav.writeframes(speech * 12 + silence * 2 + last_words * 2 + silence * 4 + after_stop)
        buffer.seek(0)
        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        with AudioFile(buffer) as source:
            audio = capture_phrase(recognizer, source, timeout=2,
                                   end_silence=END_SILENCE_SECONDS, phrase_limit=0)
            self.assertGreater(source.audio_reader.tell() / rate, 19)
            self.assertLess(source.audio_reader.tell() / rate, 20)
        self.assertIn(last_words, audio.frame_data)
        self.assertNotIn(after_stop, audio.frame_data)

    def test_manual_finish_preserves_audio_despite_continuous_noise(self):
        buffer = io.BytesIO()
        samples = b'\x10\x27' * 16000 * 30
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(samples)
        buffer.seek(0)
        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        with AudioFile(buffer) as source:
            stream = source.stream
            checks = iter([False] * 8 + [True])
            audio = capture_phrase(recognizer, source, timeout=2, end_silence=3,
                                   finish_requested=lambda: next(checks))
            self.assertIs(source.stream, stream)
            self.assertEqual(audio.frame_data, samples[:8 * source.CHUNK * 2])

    def test_finish_before_speech_returns_empty_audio_and_restores_stream(self):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b'\0\0' * 16000)
        buffer.seek(0)
        with AudioFile(buffer) as source:
            stream = source.stream
            audio = capture_phrase(Recognizer(), source, timeout=2, end_silence=3,
                                   finish_requested=lambda: True)
            self.assertEqual(audio.frame_data, b'')
            self.assertIs(source.stream, stream)

    def test_manual_finish_restores_stream_when_capture_fails(self):
        source = Mock()
        stream = source.stream
        recognizer = Mock(non_speaking_duration=0.5)
        recognizer.listen.side_effect = OSError('device disconnected')
        with self.assertRaises(OSError):
            capture_phrase(recognizer, source, timeout=2, end_silence=3,
                           finish_requested=lambda: False)
        self.assertIs(source.stream, stream)
