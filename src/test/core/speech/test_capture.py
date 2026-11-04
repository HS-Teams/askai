import io
import unittest
import wave
from unittest.mock import Mock
from speech_recognition import Recognizer, AudioFile
from askai.core.speech.capture import CaptureCancelled, END_SILENCE_SECONDS, capture_phrase


def audio_source(data, rate=16000):
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(data)
    buffer.seek(0)
    return AudioFile(buffer)


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
        with audio_source(b'\x10\x27' * 16000 * 40) as source:
            audio = capture_phrase(Recognizer(), source, timeout=2, end_silence=1.5, phrase_limit=30)
        self.assertAlmostEqual(len(audio.frame_data) / 32000, 30, delta=.02)

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
        samples = b'\x10\x27' * 16000 * 35
        with audio_source(samples) as source:
            audio = capture_phrase(Recognizer(), source, timeout=2, end_silence=1.5, tail_margin=1.5)
        self.assertEqual(audio.frame_data, samples)

    def test_dictation_preserves_short_pause_and_stops_after_shared_pause(self):
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
            self.assertGreaterEqual(source.audio_reader.tell() / rate, 16 + END_SILENCE_SECONDS)
            self.assertLess(source.audio_reader.tell() / rate, 17 + END_SILENCE_SECONDS)
        self.assertIn(last_words, audio.frame_data)
        self.assertNotIn(after_stop, audio.frame_data)

    def test_escape_discards_audio_despite_continuous_noise(self):
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
            checks = lambda: source.audio_reader.tell() >= 16000
            with self.assertRaises(CaptureCancelled):
                capture_phrase(recognizer, source, timeout=2, end_silence=END_SILENCE_SECONDS,
                               cancel_requested=checks)
            self.assertIs(source.stream, stream)
            self.assertEqual(source.audio_reader.tell(), 16000)

    def test_escape_before_speech_cancels_without_reading_audio(self):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b'\0\0' * 16000)
        buffer.seek(0)
        with AudioFile(buffer) as source:
            stream = source.stream
            with self.assertRaises(CaptureCancelled):
                capture_phrase(Recognizer(), source, timeout=2, end_silence=END_SILENCE_SECONDS,
                               cancel_requested=lambda: True)
            self.assertEqual(source.audio_reader.tell(), 0)
            self.assertIs(source.stream, stream)

    def test_cancellable_capture_preserves_stream_when_capture_fails(self):
        with audio_source(b'\0\0' * 16000) as source:
            stream = source.stream
            stream.read = Mock(side_effect=OSError('device disconnected'))
            with self.assertRaises(OSError):
                capture_phrase(Recognizer(), source, timeout=2, end_silence=3,
                               cancel_requested=lambda: False)
            self.assertIs(source.stream, stream)


class NoiseEndpointTests(unittest.TestCase):
    @staticmethod
    def samples(level, duration, rate=16000):
        import struct
        return struct.pack('<h', level) * round(rate * duration)

    def test_both_modes_exceed_ten_seconds_and_stop_despite_intermittent_noise(self):
        for rate in (16000, 44100, 48000):
            for mode, timeout in (('ptt', 3), ('dictation', None)):
                with self.subTest(rate=rate, mode=mode):
                    quiet = self.samples(50, 1, rate)
                    speech = self.samples(600, 12, rate)
                    noises = (self.samples(50, .75, rate) + self.samples(1200, .25, rate)) * 15
                    recognizer = Recognizer()
                    with audio_source(quiet + speech + noises, rate) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=.6)
                        audio = capture_phrase(recognizer, source, timeout=timeout,
                                               end_silence=END_SILENCE_SECONDS,
                                               phrase_limit=0, cancel_requested=lambda: False)
                        stopped = source.audio_reader.tell() / rate
                    self.assertIn(speech, audio.frame_data)
                    self.assertEqual(END_SILENCE_SECONDS, 2.5)
                    self.assertGreaterEqual(stopped, 13 + END_SILENCE_SECONDS)
                    self.assertLess(stopped, 13 + END_SILENCE_SECONDS + .4)
                    self.assertTrue(recognizer.dynamic_energy_threshold)

    def test_dynamic_threshold_does_not_cut_a_long_phrase_short(self):
        speech = self.samples(600, 12)
        with audio_source(speech + self.samples(50, 5)) as source:
            audio = capture_phrase(Recognizer(), source, timeout=3, end_silence=2)
            self.assertGreaterEqual(source.audio_reader.tell() / 16000, 14)
        self.assertIn(speech, audio.frame_data)

    def test_short_words_with_small_gaps_are_kept_as_a_phrase(self):
        words = (self.samples(600, .18) + self.samples(50, .08)) * 30
        with audio_source(words + self.samples(50, 5)) as source:
            audio = capture_phrase(Recognizer(), source, timeout=3, end_silence=2)
        self.assertIn(words, audio.frame_data)

    def test_short_final_word_is_not_trimmed_away(self):
        last_word = self.samples(1500, .15)
        speech = self.samples(600, 2) + self.samples(50, 1) + last_word
        with audio_source(speech + self.samples(50, 5)) as source:
            audio = capture_phrase(Recognizer(), source, timeout=3, end_silence=2)
        self.assertIn(last_word, audio.frame_data)

    def test_resuming_just_before_deadline_continues_dictation(self):
        final_words = self.samples(900, 1)
        speech = self.samples(600, 2) + self.samples(50, 2.9) + final_words
        with audio_source(speech + self.samples(50, 5)) as source:
            audio = capture_phrase(Recognizer(), source, timeout=None, end_silence=3)
            self.assertGreaterEqual(source.audio_reader.tell() / 16000, 8.9)
        self.assertIn(final_words, audio.frame_data)

    def test_initial_noise_bursts_do_not_count_as_a_phrase(self):
        from speech_recognition import WaitTimeoutError
        noise = (self.samples(900, .1) + self.samples(50, 3)) * 3
        with audio_source(noise) as source:
            with self.assertRaises(WaitTimeoutError):
                capture_phrase(Recognizer(), source, timeout=3, end_silence=2)

    def test_waiting_still_adapts_to_background_noise(self):
        from speech_recognition import WaitTimeoutError
        recognizer = Recognizer()
        with audio_source(self.samples(50, 5)) as source:
            with self.assertRaises(WaitTimeoutError):
                capture_phrase(recognizer, source, timeout=3, end_silence=2)
        self.assertLess(recognizer.energy_threshold, 300)
