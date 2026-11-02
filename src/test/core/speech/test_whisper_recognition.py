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
            'model': 'small', 'language': 'pt', 'task': 'transcribe', 'temperature': 0,
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

    def test_setting_changes_model_without_recreating_engine_and_keeps_pt_br_local(self):
        import io
        import wave
        from types import SimpleNamespace
        from unittest.mock import patch
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(b'\x00\x00' * 160)
        values = {'askai.speech.stt.whisper.model': 'small'}
        settings = SimpleNamespace(get=values.get)
        engine = RecognizerSTT('whisper')
        result = {'text': 'Olá, tudo bem?', 'segments': [{'avg_logprob': -.2}]}
        with patch.dict('sys.modules', {'askai.core.askai_settings': SimpleNamespace(settings=settings)}), patch(
                'speech_recognition.Recognizer.recognize_whisper', return_value=result) as local, patch(
                'speech_recognition.Recognizer.recognize_google') as google:
            for model in ('small', 'medium', 'large-v3'):
                values['askai.speech.stt.whisper.model'] = model
                self.assertEqual(engine.transcribe(buffer.getvalue(), 'pt_BR'), 'Olá, tudo bem?')
                self.assertEqual(local.call_args.kwargs['model'], model)
                self.assertEqual(local.call_args.kwargs['language'], 'pt')
                self.assertEqual(local.call_args.kwargs['task'], 'transcribe')
            values.clear()
            engine.transcribe(buffer.getvalue(), 'pt_BR')
            self.assertEqual(local.call_args.kwargs['model'], 'small')
            google.assert_not_called()
