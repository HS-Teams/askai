"""CLI submissions are persisted independently of textual responses."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class InputHistoryTests(unittest.TestCase):
    def test_commands_are_saved_before_execution_even_without_output(self):
        source = Path(__file__).parents[2] / 'main/askai/core/askai_cli.py'
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AskAiCli')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'run')
        order = []
        cache = Mock()
        cache.save_input_history.side_effect = lambda entries: order.append(('save', entries))
        def execute(question):
            order.append(('execute', question))
            return True, None
        scope = dict(signal=Mock(), cache=cache, configs=SimpleNamespace(is_interactive=True),
                     cli_output=Mock(), AIReply=Mock(), msg=Mock())
        exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
        view = SimpleNamespace(_query_string=None, _input=Mock(side_effect=['/gestures', '/info', '']),
                               ask_and_reply=execute, abort=Mock(), _reply=Mock())
        scope['run'](view)
        self.assertEqual(order, [('save', ['/gestures']), ('execute', '/gestures'),
                                 ('save', ['/info']), ('execute', '/info')])
        cache.save_reply.assert_not_called()
