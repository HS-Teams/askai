import ast
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import wave
from speech_recognition import Recognizer, AudioFile, WaitTimeoutError, UnknownValueError, RequestError
from askai.core.speech.capture import CaptureCancelled, capture_phrase


class DictationReadyTests(unittest.TestCase):
    def test_long_initial_silence_does_not_end_dictation(self):
        silence = b'\x00\x00' * 16000
        speech = b'\x10\x27' * 16000
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(16000)
            wav.writeframes(silence * 5 + speech * 2 + silence * 4)
        buffer.seek(0)
        recognizer = Recognizer()
        recognizer.dynamic_energy_threshold = False
        with AudioFile(buffer) as source:
            audio = capture_phrase(recognizer, source, timeout=None, end_silence=3, phrase_limit=0)
        self.assertIn(speech, audio.frame_data)

    def test_ready_is_after_calibration_and_before_capture_without_changing_normal_timeout(self):
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/component/multimedia/recorder.py'
        tree = ast.parse(path.read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'listen')
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        module = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
        mic = Mock()
        mic.return_value.__enter__ = Mock(return_value=Mock())
        mic.return_value.__exit__ = Mock(return_value=False)
        config = SimpleNamespace(stt_language='pt', recorder_silence_timeout_millis=1700,
                                 recorder_phrase_limit_millis=10000, recorder_end_silence_millis=2000,
                                 recorder_tail_margin_millis=1500)
        scope = dict(configs=config, threading=Mock(), seconds=lambda value: value / 1000,
                     Microphone=mic, msg=Mock(), Path=Path, REC_DIR='/tmp', now_ms=lambda: 0,
                     events=Mock(), WaitTimeoutError=WaitTimeoutError, UnknownValueError=UnknownValueError,
                     RequestError=RequestError)
        exec(compile(module, str(path), 'exec'), scope)
        for wait, expected, cancelled in ((True, None, False), (False, 3.0, False),
                                          (True, None, True), (False, 3.0, True)):
            order = []
            scope["events"].listening.emit.side_effect = lambda **args: order.append("visible") if args.get("listening") else None
            recorder = Mock()
            recorder._detect_noise.side_effect = lambda source: order.append('calibrate')
            def capture(*args, **kwargs):
                order.append('capture')
                self.assertEqual(kwargs['timeout'], expected)
                if cancelled:
                    raise CaptureCancelled()
                return SimpleNamespace(frame_data=b'')
            with patch('askai.core.speech.capture.capture_phrase', side_effect=capture):
                def listen():
                    return scope['listen'](recorder, wait_for_speech=wait,
                                           on_ready=lambda: order.append('ready'),
                                           on_captured=lambda: order.append('captured'))
                if cancelled:
                    with self.assertRaises(CaptureCancelled):
                        listen()
                else:
                    listen()
            self.assertEqual(order, ['calibrate', 'ready', 'visible', 'capture'] +
                             ([] if cancelled else ['captured']))
            recorder._write_audio_file.assert_not_called()
            scope['threading'].Event.return_value.set.assert_called()
            scope['threading'].Thread.return_value.join.assert_called()
            mic.return_value.__exit__.assert_called()
