import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class InitialCommentaryTests(unittest.TestCase):
    def test_both_views_present_immediately_and_enqueue_without_waiting(self):
        for filename in ('core/askai_cli.py', 'tui/askai_app.py'):
            for enabled in (True, False):
                with self.subTest(filename=filename, enabled=enabled):
                    source = Path(__file__).parents[2] / 'main/askai' / filename
                    method = next(node for node in ast.walk(ast.parse(source.read_text()))
                                  if isinstance(node, ast.FunctionDef) and node.name == '_agent_event')
                    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
                    shared = SimpleNamespace(speech=Mock(), nickname_md='Taius')
                    scope = dict(shared=shared, configs=SimpleNamespace(is_speak=enabled), log=Mock())
                    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, method], type_ignores=[])),
                                 str(source), 'exec'), scope)
                    view = Mock(mode=SimpleNamespace(icon='AI'))
                    view._display_buffer = []
                    view._agent_progress.present.side_effect = lambda render: render()
                    view.call_from_thread.side_effect = lambda fn, *args: fn(*args)
                    formatter = SimpleNamespace(console=Mock())
                    with patch('askai.cli.output.console', formatter.console), \
                         patch('askai.cli.answer_renderer.render_answer') as render:
                        scope['_agent_event'](view, SimpleNamespace(kind='initial_commentary', data={'text': 'Vou consultar.'}))
                        if filename.startswith('core'):
                            self.assertEqual(render.call_args.args[1], 'Vou consultar.')
                        else:
                            self.assertEqual(view._display_buffer, ['Taius Vou consultar.'])
                        if enabled:
                            self.assertEqual(shared.speech.speak.call_args.args[0], 'Vou consultar.')
                            self.assertFalse(shared.speech.speak.call_args.kwargs['wait'])
                            self.assertTrue(shared.speech.speak.call_args.kwargs['immediate'])
                        else:
                            shared.speech.speak.assert_not_called()
