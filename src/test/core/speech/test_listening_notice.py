import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch, call


class ListeningNoticeTests(unittest.TestCase):
    def test_listening_never_narrates_notice_even_with_speak_enabled(self):
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/support/shared_instances.py'
        tree = ast.parse(path.read_text())
        method = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'listen')
        for enabled in (True, False):
            order = []
            speech = Mock()
            speech.cancel_output.side_effect = lambda: order.append('cancel')
            speech.speak.side_effect = lambda *args, **kwargs: order.append('spoken')
            recorder = Mock()
            def capture(**kwargs):
                order.append('capture')
                return None, ' Olá '
            recorder.listen.side_effect = capture
            scope = dict(recorder=recorder, configs=SimpleNamespace(is_speak=enabled, stt_language='pt_BR'),
                         msg=Mock(listening=Mock(return_value='Listening...'),
                                  translate=Mock(return_value='Ouvindo...')))
            exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), scope)
            self.assertEqual(scope['listen'](SimpleNamespace(speech=speech)), 'Olá')
            self.assertEqual(order, ['cancel', 'capture'])
            speech.speak.assert_not_called()
            recorder.listen.assert_called_once_with(language='pt_BR')

    def test_ptt_pauses_gestures_and_releases_pause_even_on_capture_failure(self):
        from askai.gestures import background
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/support/shared_instances.py'
        method = next(n for n in ast.walk(ast.parse(path.read_text()))
                      if isinstance(n, ast.FunctionDef) and n.name == 'listen')
        for fails in (False, True):
            with self.subTest(fails=fails):
                process = Mock(poll=Mock(return_value=None))
                recorder, speech = Mock(), Mock()

                def capture(**kwargs):
                    process.stdin.write.assert_called_once_with('pause\n')
                    process.stdin.flush.assert_called_once()
                    if fails:
                        raise RuntimeError('Capture failed')
                    return None, ' Olá '

                recorder.listen.side_effect = capture
                scope = dict(recorder=recorder, configs=SimpleNamespace(stt_language='pt_BR'))
                exec(compile(ast.Module(body=[method], type_ignores=[]), str(path), 'exec'), scope)
                with patch.object(background, '_process', process):
                    if fails:
                        with self.assertRaisesRegex(RuntimeError, 'Capture failed'):
                            scope['listen'](SimpleNamespace(speech=speech))
                    else:
                        self.assertEqual(scope['listen'](SimpleNamespace(speech=speech)), 'Olá')
                self.assertEqual(process.stdin.write.call_args_list, [call('pause\n'), call('resume\n')])
