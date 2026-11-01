import unittest
from unittest.mock import Mock

from speech_recognition import UnknownValueError
from askai.core.speech.recognizer_stt import RecognizerSTT


class WhisperRecognitionTests(unittest.TestCase):
    def transcribe(self, text, scores):
        recognizer = Mock()
        recognizer.recognize_whisper.return_value = {
            'text': text, 'segments': [{'avg_logprob': score} for score in scores],
        }
        result = RecognizerSTT._transcribe_whisper(recognizer, b'audio', 'pt')
        return result, recognizer.recognize_whisper.call_args.kwargs

    def test_portuguese_is_explicit_and_decoding_does_not_sample_or_translate(self):
        text, options = self.transcribe('  Liste as vozes disponíveis. ', [-.52])
        self.assertEqual(text, 'Liste as vozes disponíveis.')
        self.assertEqual(options, {
            'language': 'pt', 'task': 'transcribe', 'temperature': 0,
            'condition_on_previous_text': False, 'show_dict': True,
            'logprob_threshold': -1.0,
        })

    def test_uncertain_speech_empty_results_and_decoder_artifacts_are_unintelligible(self):
        for text, scores in [('Bratford.', [-1.18]), ('random text', [-4.55]),
                             ('', [-.2]), ('   ', [-.2]), ('speech', []),
                             ('bridges <|ko|>', [-.3]), ('bad\ufffdtext', [-.3])]:
            with self.subTest(text=text), self.assertRaises(UnknownValueError):
                self.transcribe(text, scores)

    def test_default_whisper_confidence_boundary_is_accepted(self):
        self.assertEqual(self.transcribe('Olá.', [-1.0])[0], 'Olá.')

    def test_mixed_confidence_preserves_complete_dictation(self):
        text = 'Eu quero uma bola azul, isto e, vermelha.'
        self.assertEqual(self.transcribe(text, [-.2, -1.4])[0], text)
