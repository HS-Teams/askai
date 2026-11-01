import ast
from pathlib import Path
import re
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from click import ClickException, UsageError
from askai.core.engine.runtime import between_turns


class CommandErrorTests(unittest.TestCase):
    def test_voice_failure_is_reported_without_escaping_or_stopping_chat(self):
        source = Path(__file__).parents[2] / 'main/askai/core/askai.py'
        method = next(node for node in ast.walk(ast.parse(source.read_text()))
                      if isinstance(node, ast.FunctionDef) and node.name == 'ask_and_reply')
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        events, reply = Mock(), Mock()
        scope = dict(shared=Mock(), re=re, RE_ASKAI_CMD=r'^/.*', between_turns=between_turns, command_args=lambda match: ['voices', 'set', '1'],
                     ask_commander=Mock(side_effect=ClickException('Voice requires a paid plan')),
                     AIProcessor=object, events=events, AIReply=reply,
                     msg=SimpleNamespace(t=lambda text: text), ClickException=ClickException, UsageError=UsageError)
        for name in ('ImpossibleQuery', 'DocumentsNotFound', 'MaxInteractionsReached',
                     'InaccurateResponse', 'ValidationError'):
            scope[name] = type(name, (Exception,), {})
        module = ast.fix_missing_locations(ast.Module(body=[future, method], type_ignores=[]))
        exec(compile(module, str(source), 'exec'), scope)
        view = SimpleNamespace(mode=SimpleNamespace(processor=object()))
        with patch('askai.core.commander.command_results.execute_command', side_effect=ClickException('Voice requires a paid plan')):
            self.assertEqual(scope['ask_and_reply'](view, '/voices set 1'), (True, None))
        reply.error.assert_called_once_with('Voice requires a paid plan')
        events.reply.emit.assert_called_once_with(reply=reply.error.return_value)
