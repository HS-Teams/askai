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
