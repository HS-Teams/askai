from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from askai.core.agents.contracts import AgentError, AgentResult
from askai.core.orchestration.orchestrator import Orchestrator
from askai.core.support.persistent_memory import PersistentMemory
from askai.core.support.short_term_memory import ShortTermMemory


class SessionCompactionTests(unittest.TestCase):
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
        self.backend.compact.assert_not_called()
