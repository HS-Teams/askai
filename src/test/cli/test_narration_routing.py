import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class NarrationRoutingTests(unittest.TestCase):
    def test_cli_and_tui_synthesize_only_marked_passage(self):
        root = Path(__file__).parents[2] / 'main/askai'
        for filename in ('core/askai_cli.py', 'tui/askai_app.py'):
            for speak in (True, False):
                with self.subTest(filename=filename, speak=speak):
                    tree = ast.parse((root / filename).read_text())
                    method = next(node for node in ast.walk(tree)
                                  if isinstance(node, ast.FunctionDef) and node.name == '_reply')
                    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
                    shared = SimpleNamespace(speech=Mock(), nickname='Taius', nickname_md='Taius')
                    scope = dict(shared=shared, configs=SimpleNamespace(is_speak=speak, is_keep_context=False),
                                 msg=Mock(), display_text=Mock())
                    module = ast.fix_missing_locations(ast.Module(body=[future, method], type_ignores=[]))
                    exec(compile(module, filename, 'exec'), scope)
                    reply = SimpleNamespace(message='<TTS>Vai chover.</TTS>\nFontes: exemplo',
                                            is_final=True, is_speakable=True)
                    view = Mock(mode=SimpleNamespace(icon='AI'))
                    view._display_buffer = []
                    formatter = SimpleNamespace(text_formatter=SimpleNamespace(console=Mock()))
                    with patch.dict('sys.modules', {'askai.core.support.text_formatter': formatter}), \
                         patch('askai.cli.answer_renderer.render_answer') as render:
                        scope['_reply'](view, reply)
                        if speak:
                            self.assertEqual(shared.speech.speak.call_args.args[0], 'Vai chover.')
                        else:
                            shared.speech.speak.assert_not_called()
                            visible = render.call_args.args[1] if filename.startswith('core') else view._display_buffer[0]
                            self.assertIn('降 Vai chover.', visible)
                            self.assertIn('Fontes: exemplo', visible)
                            self.assertNotIn('<TTS>', visible)
