from threading import Event
from contextlib import nullcontext
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from askai.core.agents.codex import CodexBackend
from askai.core.agents.contracts import AgentTask
from askai.core.support.communication import CommunicationBus


class CommandDispatchTests(unittest.TestCase):
    def test_visible_agent_commentary_also_reaches_the_session_bus(self):
        transport = Mock()
        transport.receive.side_effect = [
            {'method': 'item/completed', 'params': {'item': {
                'type': 'agentMessage', 'phase': 'commentary', 'text': 'Checking voices'}}},
            {'method': 'item/completed', 'params': {'item': {
                'type': 'agentMessage', 'phase': 'final_answer', 'id': 'answer', 'text': 'Done'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 'turn', 'status': 'completed'}}},
        ]
        bus, emit = CommunicationBus(), Mock()
        with patch('askai.core.support.communication.communication', bus):
            CodexBackend()._consume(transport, 'session', 'turn', emit, Mock(), Event())
        self.assertEqual(bus.recent()[0]['kind'], 'agent.commentary')
        self.assertEqual(bus.recent()[0]['payload']['message'], 'Checking voices')
        commentary = [call.args[0] for call in emit.call_args_list if call.args[0].kind == 'initial_commentary']
        self.assertEqual(len(commentary), 1)
        self.assertEqual(commentary[0].data['text'], 'Checking voices')

    def test_command_tool_is_registered_without_loading_command_catalogue(self):
        transport = Mock()
        transport.request.side_effect = lambda method, params: (
            {'thread': {'id': 'session'}} if method == 'thread/start' else {'turn': {'id': 'turn'}})
        backend = CodexBackend()
        backend._connections = Mock()
        backend._connections.lease.return_value = nullcontext(transport)
        with patch('askai.core.agents.codex.prepared_input', return_value=nullcontext('hello')), \
             patch.object(backend, '_consume', return_value=Mock()):
            backend.run(AgentTask('hello', Path.cwd()), Mock(), Mock(), Event())
        options = next(call.args[1] for call in transport.request.call_args_list if call.args[0] == 'thread/start')
        self.assertIn('askai_command', [tool['name'] for tool in options['dynamicTools']])
        self.assertIn('action=help', options['developerInstructions'])
        self.assertNotIn('AskAI Commander - HELP', options['developerInstructions'])

    def test_host_command_is_dispatched_only_in_execution_turns(self):
        for allowed in (True, False):
            with self.subTest(allowed=allowed):
                transport = Mock()
                transport.receive.side_effect = [
                    {'id': 77, 'method': 'item/tool/call',
                     'params': {'tool': 'askai_command', 'arguments': {'action': 'help'}}},
                    {'method': 'item/completed', 'params': {'item': {
                        'type': 'agentMessage', 'phase': 'final_answer', 'id': 'answer', 'text': 'Done'}}},
                    {'method': 'turn/completed', 'params': {'turn': {'id': 'turn', 'status': 'completed'}}},
                ]
                with patch('askai.core.agents.codex.askai_command', return_value={'success': True}) as tool:
                    CodexBackend()._consume(transport, 'session', 'turn', Mock(), Mock(), Event(), allow_tools=allowed)
                self.assertEqual(tool.call_count, int(allowed))
                self.assertEqual(transport.send.call_args.args[0]['result']['success'], allowed)
