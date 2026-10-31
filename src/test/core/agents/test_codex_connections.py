import unittest
from unittest.mock import Mock
from askai.core.agents.codex_connections import CodexConnections
from askai.core.agents.contracts import AgentError


class ConnectionTests(unittest.TestCase):
    def transport(self):
        result = Mock()
        result.__enter__ = Mock(return_value=result)
        result.__exit__ = Mock()
        result.request.return_value = {'account': {'type': 'chatgpt'}}
        return result

    def test_reuses_process_and_separates_review_permissions(self):
        execution, review = self.transport(), self.transport()
        factory = Mock(side_effect=[execution, review, self.transport()])
        connections = CodexConnections('codex', factory)
        self.addCleanup(connections.close)
        connections.prepare()
        with connections.lease(False) as first:
            self.assertIs(first, execution)
        with connections.lease(True) as second:
            self.assertIs(second, review)
        with connections.lease(True) as third:
            self.assertIs(third, second)
        self.assertEqual(factory.call_count, 2)
        self.assertIn('mcp_servers.askai_desktop.enabled=false', factory.call_args_list[1].args[0])
        self.assertEqual([c.args[0] for c in execution.request.call_args_list], ['initialize', 'account/read'])
        connections.close()
        execution.__exit__.assert_called_once()
        review.__exit__.assert_called_once()

    def test_failure_discards_connection_without_retrying_action(self):
        broken, fresh = self.transport(), self.transport()
        factory = Mock(side_effect=[broken, fresh])
        connections = CodexConnections('codex', factory)
        self.addCleanup(connections.close)
        with self.assertRaises(AgentError), connections.lease(False):
            raise AgentError('Turn failed')
        factory.assert_called_once()
        broken.__exit__.assert_called_once()
        with connections.lease(False) as connection:
            self.assertIs(connection, fresh)

    def test_failed_login_closes_process(self):
        transport = self.transport()
        transport.request.return_value = {'account': {'type': 'apiKey'}}
        connections = CodexConnections('codex', Mock(return_value=transport))
        with self.assertRaises(AgentError):
            connections.prepare()
        transport.__exit__.assert_called_once()
