"""Exercise both actual notification handlers without loading audio devices."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class FallbackNoticeTests(unittest.TestCase):
    def handler(self, filename, scope):
        path = Path(__file__).parents[2] / 'main/askai' / filename
        tree = ast.parse(path.read_text())
        method = next(node for node in ast.walk(tree)
                      if isinstance(node, ast.FunctionDef) and node.name == '_cb_tts_fallback')
        method.args.args[1].annotation = None
        module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
        exec(compile(module, str(path), 'exec'), scope)
        return scope['_cb_tts_fallback']

    def test_cli_and_tui_translate_complete_message_without_interpreting_translated_braces(self):
        for filename in ('core/askai_cli.py', 'tui/askai_app.py'):
            with self.subTest(filename=filename):
                translated = 'Troca para Ollama: {provedor}, motivo {motivo}.'
                translator = Mock(return_value=translated)
                display = Mock()
                view = Mock()
                handler = self.handler(filename, {'msg': SimpleNamespace(t=translator), 'cli_output': SimpleNamespace(render_text=display)})
                event = SimpleNamespace(args=SimpleNamespace(provider='ElevenLabs', reason='HTTP 402'))
                handler(view, event)
                translator.assert_any_call(
                    'TTS switched from ElevenLabs to Ollama. Reason: HTTP 402. '
                    'The configured default was not changed.')
                if filename.startswith('core'):
                    self.assertEqual(translated, display.call_args.args[0])
                    self.assertTrue(display.call_args.args[1].startswith('⚠ '))
                    self.assertTrue(display.call_args.args[1].endswith(' · TTS'))
                    self.assertEqual(display.call_args.kwargs['style'], 'yellow')
                else:
                    self.assertEqual(str(view.call_later.call_args.args[1]), translated)
                    self.assertIsInstance(view.call_later.call_args.args[1], str)
                    self.assertIsInstance(view.call_later.call_args.kwargs['title'], str)
                    self.assertFalse(view.call_later.call_args.kwargs['markup'])
                view._reply.assert_not_called()

    def test_cli_defers_startup_notice_until_splash_is_finished(self):
        translator, display = Mock(return_value='translated reason'), Mock()
        handler = self.handler('core/askai_cli.py', {
            'msg': SimpleNamespace(t=translator), 'cli_output': SimpleNamespace(render_text=display),
        })
        view = SimpleNamespace(_ready=False)
        event = SimpleNamespace(args=SimpleNamespace(provider='ElevenLabs', reason='HTTP 402'))
        handler(view, event)
        display.assert_not_called()
        translator.assert_not_called()
        self.assertIs(view._pending_tts_fallback, event)
        view._ready = True
        handler(view, view._pending_tts_fallback)
        display.assert_called_once()
