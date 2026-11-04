import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock, patch
from askai.core.agents.codex_connections import CodexConnections
from askai.core.agents.contracts import AgentError
from askai.core.permissions.grants import GrantDenied, GrantPolicy


class ConnectionTests(unittest.TestCase):
    def test_nested_read_only_lease_restores_execution_without_allowing_escalation(self):
        connections = CodexConnections('codex', Mock(return_value=self.transport()))
        self.addCleanup(connections.close)
        with connections.lease(False):
            with connections.lease(False, actions_allowed=False):
                self.assertEqual(connections._scope_file.read_text(), 'deny')
                with self.assertRaisesRegex(AgentError, 'Cannot enable actions'):
                    with connections.lease(False):
                        self.fail('Nested execution must not begin')
                self.assertEqual(connections._scope_file.read_text(), 'deny')
            self.assertEqual(connections._scope_file.read_text(), 'allow')
        self.assertEqual(connections._scope_file.read_text(), 'deny')

    def test_cancellation_revokes_enclosing_leases_as_well(self):
        connections = CodexConnections('codex', Mock(return_value=self.transport()))
        self.addCleanup(connections.close)
        with connections.lease(False):
            with connections.lease(True):
                connections.revoke_actions()
            self.assertEqual(connections._scope_file.read_text(), 'deny')
            with self.assertRaisesRegex(AgentError, 'Cannot enable actions'):
                with connections.lease(False):
                    self.fail('Cancellation must not be reversible inside the turn')
        with connections.lease(False):
            self.assertEqual(connections._scope_file.read_text(), 'allow')

    def test_failed_process_scope_is_removed_before_shutdown_and_never_reused(self):
        broken, fresh = self.transport(), self.transport()
        connections = CodexConnections('codex', Mock(side_effect=[broken, fresh]))
        self.addCleanup(connections.close)
        with self.assertRaisesRegex(AgentError, 'failed'), connections.lease(False):
            old_scope = connections._scope_file
            broken.__exit__.side_effect = lambda *args: self.assertFalse(old_scope.exists())
            raise AgentError('failed')
        with connections.lease(False):
            self.assertNotEqual(old_scope, connections._scope_file)
            with patch.dict('os.environ', {'ASKAI_ACTION_SCOPE_FILE': str(old_scope)}):
                with self.assertRaises(GrantDenied):
                    GrantPolicy(lambda key: 'allow').pending(['media.play.local'])

    def test_scope_write_failure_closes_connection_and_removes_stale_allow(self):
        transport = self.transport()
        connections = CodexConnections('codex', Mock(return_value=transport))
        self.addCleanup(connections.close)
        with self.assertRaises(OSError):
            with connections.lease(False):
                scope = connections._scope_file
                patcher = patch.object(connections, '_set_action_scope', side_effect=OSError('cannot revoke'))
                patcher.start()
                self.addCleanup(patcher.stop)
        self.assertFalse(scope.exists())
        transport.__exit__.assert_called_once()

    def test_shutdown_error_does_not_leave_permissions_or_connection_alive(self):
        transport = self.transport()
        transport.__exit__.side_effect = OSError('shutdown failed')
        connections = CodexConnections('codex', Mock(return_value=transport))
        self.addCleanup(connections.close)
        connections.prepare()
        scope = connections._scope_file
        with self.assertRaisesRegex(OSError, 'shutdown failed'):
            connections.close()
        self.assertFalse(scope.exists())
        self.assertIsNone(connections._connection)
        self.assertFalse(connections._registered)

    def test_nested_failure_cannot_reopen_a_server_during_the_outer_turn(self):
        factory = Mock(return_value=self.transport())
        connections = CodexConnections('codex', factory)
        self.addCleanup(connections.close)
        with connections.lease(False):
            with self.assertRaisesRegex(AgentError, 'inner failed'), connections.lease(True):
                raise AgentError('inner failed')
            with self.assertRaisesRegex(AgentError, 'active lease'):
                connections.prepare()
        factory.assert_called_once()

    def transport(self):
        result = Mock()
        result.__enter__ = Mock(return_value=result)
        result.__exit__ = Mock()
        result.request.return_value = {'account': {'type': 'chatgpt'}}
        return result

    def test_reuses_process_and_separates_review_permissions(self):
        execution = self.transport()
        factory = Mock(return_value=execution)
        connections = CodexConnections('codex', factory)
        self.addCleanup(connections.close)
        connections.prepare()
        with patch.dict('os.environ', {'ASKAI_ACTION_SCOPE_FILE': str(connections._scope_file)}):
            policy = GrantPolicy(lambda key: 'allow')
            for read_only in (False, True, True, False):
                with connections.lease(read_only) as connection:
                    self.assertIs(connection, execution)
                    if read_only:
                        with self.assertRaises(GrantDenied):
                            policy.pending(['media.play.local'])
                    else:
                        self.assertEqual(policy.pending(['media.play.local']), [])
                with self.assertRaises(GrantDenied):
                    policy.pending(['media.play.local'])
        factory.assert_called_once()
        self.assertEqual([c.args[0] for c in execution.request.call_args_list], ['initialize', 'account/read'])
        connections.close()
        execution.__exit__.assert_called_once()

    def test_concurrent_startup_and_request_initialize_only_once(self):
        factory = Mock(return_value=self.transport())
        connections = CodexConnections('codex', factory)
        self.addCleanup(connections.close)
        barrier = Barrier(2)
        def prepare():
            barrier.wait(timeout=2)
            return connections.prepare()
        with ThreadPoolExecutor(max_workers=2) as pool:
            first, second = pool.submit(prepare), pool.submit(prepare)
            self.assertIs(first.result(), second.result())
        factory.assert_called_once()

    def test_failed_process_start_cleans_scope_and_can_prepare_again(self):
        broken, fresh = self.transport(), self.transport()
        broken.__enter__.side_effect = AgentError('Cannot start Codex')
        connections = CodexConnections('codex', Mock(side_effect=[broken, fresh]))
        self.addCleanup(connections.close)
        with self.assertRaises(AgentError):
            connections.prepare()
        self.assertIsNone(connections._scope_directory)
        self.assertIs(connections.prepare(), fresh)

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

    def test_private_review_shares_process_but_revokes_desktop_actions(self):
        connection = self.transport()
        connections = CodexConnections('codex', Mock(return_value=connection))
        self.addCleanup(connections.close)
        with connections.lease(False, actions_allowed=True):
            self.assertEqual(connections._scope_file.read_text(), 'allow')
        self.assertEqual(connections._scope_file.read_text(), 'deny')
        with connections.lease(False, actions_allowed=False):
            self.assertEqual(connections._scope_file.read_text(), 'deny')
