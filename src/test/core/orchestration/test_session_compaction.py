from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from askai.core.agents.contracts import AgentError, AgentResult, AgentSessionNotFound
from askai.core.orchestration.orchestrator import Orchestrator
from askai.core.support.persistent_memory import PersistentMemory
from askai.core.support.short_term_memory import ShortTermMemory


class SessionCompactionTests(unittest.TestCase):
    def test_missing_previous_session_does_not_block_new_day_or_erase_history(self):
        self.service._today = lambda: date(2026, 11, 3)
        self.request()
        history = self.durable.conversations('codex', str(self.cwd))
        self.backend.compact.side_effect = AgentSessionNotFound('rollout removed')
        self.backend.run.return_value = AgentResult('new', 't2', 'Next answer', 'completed')
        self.service._today = lambda: date(2026, 11, 4)

        self.request()

        self.assertIsNone(self.backend.run.call_args.args[0].session_id)
        self.assertIsNone(self.durable.session('codex', str(self.cwd), '2026-11-03'))
        self.assertEqual(self.durable.session('codex', str(self.cwd), '2026-11-04'), 'new')
        self.assertNotIn((str(self.cwd), '2026-11-03'), self.service._sessions)
        self.assertEqual(self.durable.conversations('codex', str(self.cwd))[:len(history)], history)
        self.request()
        self.backend.compact.assert_called_once()

    def test_daily_rotation_compacts_previous_session_before_new_execution(self):
        self.service._today = lambda: date(2026, 11, 3)
        self.request()
        self.backend.reset_mock()
        self.backend.run.return_value = AgentResult('new', 't', 'Answer', 'completed')
        self.service._today = lambda: date(2026, 11, 4)
        self.request()
        calls = [call[0] for call in self.backend.mock_calls if call[0] in {'compact', 'run'}]
        self.assertEqual(calls, ['compact', 'run'])
        self.backend.compact.assert_called_once_with('s', self.cwd, None)
        self.assertIsNone(self.backend.run.call_args.args[0].session_id)
        self.assertEqual(self.durable.session('codex', str(self.cwd), '2026-11-03'), 's')
        self.request()
        self.assertEqual(self.backend.compact.call_count, 1)

    def test_restart_on_new_day_compacts_saved_session_without_using_another_scope(self):
        self.service._today = lambda: date(2026, 11, 3)
        self.request()
        self.durable.record('other', str(self.cwd), 'other', 'completed', {}, 'unrelated',
                            session_date='2026-11-03')
        restarted = Orchestrator(self.backend, ShortTermMemory(4), lambda q: '', Mock(),
                                 lambda q, a, r: a, durable=PersistentMemory(self.durable.path),
                                 today=lambda: date(2026, 11, 4))
        restarted.process('Next', self.cwd, '', Mock(), Mock())
        self.backend.compact.assert_called_once_with('s', self.cwd, None)

    def test_rotation_failure_preserves_previous_session_and_does_not_start_new_turn(self):
        self.service._today = lambda: date(2026, 11, 3)
        self.request()
        self.backend.compact.side_effect = AgentError('offline')
        self.service._today = lambda: date(2026, 11, 4)
        with self.assertRaisesRegex(AgentError, 'offline'):
            self.request()
        self.assertEqual(self.backend.run.call_count, 1)
        self.assertEqual(self.durable.session('codex', str(self.cwd), '2026-11-03'), 's')
        self.assertIsNone(self.durable.session('codex', str(self.cwd), '2026-11-04'))

    def test_manual_compaction_is_not_repeated_before_reset_without_new_activity(self):
        self.request()
        self.service.compact_session(self.cwd, Mock())
        self.service.reset_session(self.cwd)
        self.backend.compact.assert_called_once()
        self.backend.archive.assert_called_once_with('s')

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.cwd = Path(self.directory.name).resolve()
        self.durable = PersistentMemory(self.cwd / 'memory.sqlite3')
        self.backend = Mock()
        self.backend.run.return_value = AgentResult('s', 't', 'Answer', 'completed')
        self.stm = ShortTermMemory(4)
        self.service = Orchestrator(self.backend, self.stm, lambda q: '', Mock(),
                                    lambda q, a, r: a, durable=self.durable)

    def request(self):
        self.service.process('Question', self.cwd, '', Mock(), Mock())

    def test_compacts_once_per_revision_preserving_session_history_and_stm(self):
        self.request()
        messages = list(self.stm.messages)
        history = self.durable.conversations('codex', str(self.cwd))
        self.assertTrue(self.service.compact_session(self.cwd, Mock()))
        self.assertFalse(self.service.compact_session(self.cwd, Mock()))
        self.backend.compact.assert_called_once_with('s', self.cwd, None)
        self.assertEqual(self.durable.session('codex', str(self.cwd)), 's')
        self.assertEqual(self.stm.messages, messages)
        self.assertEqual(self.durable.conversations('codex', str(self.cwd)), history)
        self.request()
        self.assertTrue(self.service.compact_session(self.cwd, Mock()))
        self.assertEqual(self.backend.compact.call_count, 2)

    def test_compacted_revision_survives_restart(self):
        self.request()
        self.service.compact_session(self.cwd, Mock())
        from askai.core.orchestration.session_compaction import compact_saved_session
        self.assertFalse(compact_saved_session(self.backend, PersistentMemory(self.durable.path),
                                               'codex', str(self.cwd), date.today().isoformat(), Mock()))
        self.backend.compact.assert_called_once()

    def test_failure_does_not_mark_revision_compacted(self):
        self.request()
        self.backend.compact.side_effect = AgentError('failed')
        with self.assertRaises(AgentError):
            self.service.compact_session(self.cwd, Mock())
        latest, compacted = self.durable.compaction_revision('codex', str(self.cwd), 's')
        self.assertGreater(latest, compacted)
        self.assertEqual(self.durable.session('codex', str(self.cwd)), 's')

    def test_empty_reset_and_busy_sessions_do_not_compact(self):
        self.assertFalse(self.service.compact_session(self.cwd, Mock()))
        self.request()
        self.service.reset_session(self.cwd)
        self.assertFalse(self.service.compact_session(self.cwd, Mock()))
        self.service._active.acquire()
        try:
            with self.assertRaisesRegex(AgentError, 'Wait for'):
                self.service.compact_session(self.cwd, Mock())
        finally:
            self.service._active.release()
        self.backend.compact.assert_called_once_with('s', self.cwd, None)
