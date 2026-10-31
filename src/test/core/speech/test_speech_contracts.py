import io
import unittest
import wave
from unittest.mock import Mock, patch

from askai.core.speech import STTEngine, TTSEngine
from askai.core.speech.factory import create_stt, create_tts
from askai.core.speech.service import SpeechService
from askai.core.engine.llama.llama_speech import LlamaSpeech


class SpeechContractTests(unittest.TestCase):
    def test_capabilities_are_lazy_independent_and_reused(self):
        with patch("askai.core.speech.service.create_stt") as stt, patch(
            "askai.core.speech.service.create_tts"
        ) as tts:
            service = SpeechService("google", "ollama")
            stt.assert_not_called()
            tts.assert_not_called()
            self.assertIs(service.stt, service.stt)
            stt.assert_called_once_with("google")
            tts.assert_not_called()
            self.assertIs(service.tts, service.tts)
            tts.assert_called_once_with("ollama")

    def test_existing_providers_satisfy_contracts(self):
        self.assertIsInstance(create_stt(" Google "), STTEngine)
        self.assertIsInstance(create_stt("WHISPER"), STTEngine)
        self.assertIsInstance(LlamaSpeech(Mock(), Mock()), TTSEngine)

    def test_unknown_providers_fail_without_fallback(self):
        for factory in (create_stt, create_tts):
            with self.subTest(factory=factory.__name__):
                with self.assertRaises(ValueError):
                    factory("elevenlabs")

    def test_stt_transcribes_wav_without_capturing_microphone(self):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 160)
        for provider in ("google", "whisper"):
            with self.subTest(provider=provider), patch(
                f"speech_recognition.Recognizer.recognize_{provider}",
                return_value="ola",
            ) as recognize:
                self.assertEqual(
                    create_stt(provider).transcribe(buffer.getvalue(), "pt"), "ola"
                )
                audio = recognize.call_args.args[0]
                self.assertEqual(audio.sample_rate, 16000)
                self.assertEqual(recognize.call_args.kwargs, {"language": "pt"})

    def test_invalid_wav_does_not_call_provider(self):
        with patch("speech_recognition.Recognizer.recognize_google") as recognize:
            with self.assertRaises(ValueError):
                create_stt("google").transcribe(b"not audio", "pt")
            recognize.assert_not_called()


class SpeechLanguageTests(unittest.TestCase):
    def test_locale_is_adapted_for_each_provider(self):
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b"\x00\x00" * 160)
        for provider, language in (("google", "pt-BR"), ("whisper", "pt")):
            with self.subTest(provider=provider), patch(
                f"speech_recognition.Recognizer.recognize_{provider}", return_value="liste meus downloads"
            ) as recognize:
                self.assertEqual(create_stt(provider).transcribe(buffer.getvalue(), "pt_BR"), "liste meus downloads")
                self.assertEqual(recognize.call_args.kwargs, {"language": language})
