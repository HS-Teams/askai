import json
from threading import Event
from types import ModuleType
import unittest
from unittest.mock import Mock, patch

import click

from askai.core.agents.command_tool import askai_command
from askai.core.commander.agent_commands import command_requests


class CommandToolTests(unittest.TestCase):
    def setUp(self):
        self.commander = ModuleType('askai.core.commander.commander')
        self.commander.ask_commander = click.Group()
        for name in ('help', 'dictate', 'settings', 'grants', 'voices', 'engine', 'model'):
            self.commander.ask_commander.add_command(click.Command(name))
        self.commander.commander_help = Mock(return_value='Command usage')
        self.modules = patch.dict('sys.modules', {self.commander.__name__: self.commander})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.execute = patch('askai.core.agents.command_tool.execute_command',
                             side_effect=lambda args: {'status': 'completed', 'command': args[0]})
        self.executor = self.execute.start()
        self.addCleanup(self.execute.stop)
        self.cancelled = Event()

    def call(self, **arguments):
        result = askai_command({'arguments': arguments}, Mock(), Mock(), self.cancelled)
        return json.loads(result['contentItems'][0]['text'])

    def test_help_is_on_demand_without_execution(self):
        self.assertEqual(self.call(action='help')['help'], 'Command usage')
        self.commander.commander_help.assert_called_once_with(None)
        self.call(action='help', command='/dictate')
        self.commander.commander_help.assert_called_with('dictate')

    def test_execute_queues_tokens_in_current_session_without_running_command(self):
        with command_requests() as pending:
            result = self.call(action='execute', command='/dictate', arguments=['--dest-file', '/tmp/my dictation.txt'])
            self.assertEqual(result['status'], 'queued')
            self.assertEqual(pending, [(['dictate', '--dest-file', '/tmp/my dictation.txt'], self.cancelled)])
        with self.assertRaisesRegex(ValueError, 'No active'):
            self.call(action='execute', command='dictate')

    def test_cancelled_request_is_not_queued(self):
        self.cancelled.set()
        with command_requests() as pending:
            self.assertEqual(self.call(action='execute', command='dictate')['status'], 'cancelled')
        self.assertEqual(pending, [])

    def test_nested_sessions_keep_their_own_requests(self):
        with command_requests() as outer:
            self.call(action='execute', command='dictate')
            with command_requests() as inner:
                self.call(action='execute', command='dictate')
            self.assertEqual(len(outer), 1)
            self.assertEqual(inner[0][0], ['dictate'])

    def test_invalid_requests_never_queue(self):
        for arguments in ({'action': 'execute', 'command': 'not-a-command'},
                          {'action': 'shell', 'command': 'help'},
                          {'action': 'execute', 'command': 'help', 'arguments': 'hello'},
                          {'action': 'help', 'extra': True},
                          {'action': 'help', 'arguments': ['unexpected']}):
            with self.subTest(arguments=arguments), command_requests() as pending:
                with self.assertRaises(ValueError):
                    self.call(**arguments)
                self.assertEqual(pending, [])

    def test_commands_cannot_rewrite_permissions(self):
        for command, arguments in [('grants', ['set', 'camera.capture.local', 'allow']),
                                   ('grants', ['reset']), ('settings', ['RESET']),
                                   ('settings', ['--', 'SET', 'askai.grants.camera.capture.local', 'allow']),
                                   ('settings', ['set', '42', 'allow'])]:
            with self.subTest(command=command, arguments=arguments), command_requests() as pending:
                with self.assertRaises(ValueError):
                    self.call(action='execute', command=command, arguments=arguments)
                self.assertEqual(pending, [])

    def test_nonpermission_settings_and_grant_reads_are_available(self):
        with command_requests() as pending:
            self.call(action='execute', command='settings', arguments=['set', 'askai.speak.enabled', 'true'])
            self.call(action='execute', command='grants', arguments=['list'])
        self.assertEqual(len(pending), 0)
        self.assertEqual(self.executor.call_count, 2)

    def test_voice_selection_returns_result_in_the_same_turn(self):
        self.executor.side_effect = None
        self.executor.return_value = {'status': 'completed', 'data': {'selected_voice': 'Voice 12'}}
        with command_requests() as pending:
            result = self.call(action='execute', command='voices', arguments=['set', '12'])
        self.assertEqual(result['data']['selected_voice'], 'Voice 12')
        self.executor.assert_called_once_with(['voices', 'set', '12'])
        self.assertEqual(pending, [])

    def test_runtime_selections_are_deferred_until_the_agent_turn_ends(self):
        with command_requests() as pending:
            for command, name in [('engine', 'codex'), ('model', 'model-b')]:
                result = self.call(action='execute', command=command, arguments=['set', name])
                self.assertEqual(result['status'], 'queued')
        self.assertEqual([request[0] for request in pending],
                         [['engine', 'set', 'codex'], ['model', 'set', 'model-b']])
        self.executor.assert_not_called()

    def test_state_returns_structured_catalogue_without_executing(self):
        with patch('askai.core.agents.command_tool.current_state', return_value={'voices': [{'index': 12, 'name': 'Alice'}]}) as state:
            result = self.call(action='state', command='voices')
        self.assertEqual(result['data']['voices'][0]['index'], 12)
        state.assert_called_once_with('voices')
        self.executor.assert_not_called()

    def test_failed_state_can_be_diagnosed_without_loading_app_services_again(self):
        with patch('askai.core.agents.command_tool.current_state', side_effect=RuntimeError('voice API unavailable')):
            result = self.call(action='state', command='voices')
        self.assertEqual(result['status'], 'failed')
        diagnostics = self.call(action='diagnostics', command='voices')
        self.assertEqual(diagnostics['data']['source'], 'current_process_command_log')
        self.assertEqual(diagnostics['data']['entries'][-1]['error'], 'voice API unavailable')
