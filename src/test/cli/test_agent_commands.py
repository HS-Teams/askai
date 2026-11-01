"""Exercise command scheduling through the real application request method."""
import ast
from pathlib import Path
import re
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from click import ClickException, UsageError
from askai.core.commander.agent_commands import queue_command
from askai.core.engine.runtime import between_turns


class AgentCommandExecutionTests(unittest.TestCase):
    def run_request(self, *, cancel=False, fail=False):
        source = Path(__file__).parents[2] / 'main/askai/core/askai.py'
        method = next(node for node in ast.walk(ast.parse(source.read_text()))
                      if isinstance(node, ast.FunctionDef) and node.name == 'ask_and_reply')
        order = []
        cancelled = Event()

        def process(*args, **kwargs):
            queue_command('dictate', [], cancelled)
            order.append('agent finished')
            if cancel:
                cancelled.set()
            return 'Command queued.'

        def execute(*args, **kwargs):
            order.append('command executed')
            if fail:
                raise UsageError('Invalid command arguments')

        processor = SimpleNamespace(cacheable=False, process=process)
        events = Mock()
        scope = dict(shared=Mock(), re=re, RE_ASKAI_CMD=r'^/.*', between_turns=between_turns,
                     ask_commander=Mock(side_effect=execute), AIProcessor=object,
                     events=events, AIReply=Mock(), cache=Mock(), log=Mock(),
                     msg=Mock(translate_response=lambda text, question: text), read_stdin=lambda: '',
                     ClickException=ClickException, UsageError=UsageError)
        for name in ('ImpossibleQuery', 'DocumentsNotFound', 'MaxInteractionsReached',
                     'InaccurateResponse', 'ValidationError', 'IntelligibleAudioError',
                     'RateLimitError', 'TerminatingQuery'):
            scope[name] = type(name, (Exception,), {})
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        module = ast.fix_missing_locations(ast.Module(body=[future, method], type_ignores=[]))
        exec(compile(module, str(source), 'exec'), scope)
        view = SimpleNamespace(mode=SimpleNamespace(processor=processor), engine=Mock(), _query_prompt=None)
        with patch('askai.core.commander.command_results.execute_command', side_effect=execute) as executor, \
             patch('askai.core.engine.runtime.response_cache_key', side_effect=lambda question: question):
            scope['ask_and_reply'](view, 'ative o ditado')
        scope['executor'] = executor
        return scope, order

    def test_command_runs_in_current_app_after_agent_returns(self):
        scope, order = self.run_request()
        self.assertEqual(order, ['agent finished', 'command executed'])
        scope['executor'].assert_called_once_with(['dictate'], raise_errors=True)

    def test_cancelled_turn_does_not_execute_queued_commands(self):
        scope, order = self.run_request(cancel=True)
        self.assertEqual(order, ['agent finished'])
        scope['executor'].assert_not_called()

    def test_command_errors_follow_existing_app_error_reporting(self):
        scope, _ = self.run_request(fail=True)
        scope['msg'].invalid_command.assert_called_once()
        scope['AIReply'].error.assert_called_once()
