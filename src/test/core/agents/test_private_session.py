from pathlib import Path
from threading import Event
import unittest
from unittest.mock import Mock, patch
from askai.core.agents.codex import CodexBackend
from askai.core.agents.contracts import AgentTask


class PrivateSessionTests(unittest.TestCase):
    def test_private_turns_share_connection_without_disk_resume(self):
        backend = CodexBackend()
        transport = Mock()
        transport.request.side_effect = lambda method, params: (
            {'thread': {'id': 'private'}, 'model': 'test'} if method == 'thread/start'
            else {'turn': {'id': 'turn'}})
        lease = Mock()
        lease.__enter__ = Mock(return_value=transport)
        lease.__exit__ = Mock(return_value=False)
        backend._connections = Mock()
        backend._connections.lease.return_value = lease
        with patch.object(backend, '_consume', return_value=Mock()):
            backend.run(AgentTask('hello', Path.cwd(), persist_history=False), Mock(), Mock(), Event())
            backend.run(AgentTask('review', Path.cwd(), session_id='private', read_only=True,
                                  persist_history=False), Mock(), Mock(), Event())
        methods = [c.args[0] for c in transport.request.call_args_list]
        self.assertEqual(methods, ['thread/start', 'turn/start', 'turn/start'])
        self.assertTrue(transport.request.call_args_list[0].args[1]['ephemeral'])
        options = transport.request.call_args_list[-1].args[1]
        self.assertEqual(options['sandboxPolicy'], {'type': 'readOnly'})
        self.assertEqual(options['approvalPolicy'], 'never')
        self.assertTrue(backend.session_is_private('private'))
        self.assertEqual([c.args for c in backend._connections.lease.call_args_list], [(False,), (False,)])

        self.assertEqual([c.kwargs for c in backend._connections.lease.call_args_list],
                         [{'actions_allowed': True}, {'actions_allowed': False}])
