import unittest
from unittest.mock import Mock
from pathlib import Path
from askai.core.orchestration.session_reset import reset_saved_session
from askai.core.orchestration.orchestrator import Orchestrator
from askai.core.agents.contracts import AgentSessionNotFound, AgentResult
from askai.core.support.persistent_memory import PersistentMemory
from askai.core.support.short_term_memory import ShortTermMemory
from tempfile import TemporaryDirectory


class SessionResetTests(unittest.TestCase):
    def test_missing_session_during_compaction_or_archive_allows_clean_next_request(self):
        for operation in ('compact', 'archive'):
            with self.subTest(operation=operation), TemporaryDirectory() as directory:
                cwd = Path(directory).resolve()
                durable = PersistentMemory(cwd / 'memory.sqlite3')
                backend = Mock()
                backend.run.return_value = AgentResult('lost', 't', 'Old answer', 'completed')
                memory = ShortTermMemory(4)
                service = Orchestrator(backend, memory, lambda q: '', Mock(),
                                       lambda q, a, r: a, durable=durable)
                service.process('First', cwd, '', Mock(), Mock())
                saved_messages = list(memory.messages)
                getattr(backend, operation).side_effect = AgentSessionNotFound('no rollout found')
                service.reset_session(cwd)
                self.assertFalse(service._sessions)
                self.assertIsNone(durable.session('codex', str(cwd)))
                self.assertEqual(memory.messages, saved_messages)
                self.assertEqual(durable.conversations('codex', str(cwd))[0]['answer'], 'Old answer')
                if operation == 'compact':
                    backend.archive.assert_not_called()
                backend.run.return_value = AgentResult('new', 't2', 'New answer', 'completed')
                service.process('Next', cwd, '', Mock(), Mock())
                self.assertIsNone(backend.run.call_args.args[0].session_id)
                self.assertEqual(durable.session('codex', str(cwd)), 'new')

    def test_compaction_failure_preserves_session_without_archiving(self):
        backend, memory = Mock(), Mock()
        memory.compaction_revision.return_value = (1, 0)
        backend.compact.side_effect = RuntimeError('offline')
        service = Orchestrator(backend, Mock(), Mock(), Mock(), Mock(), durable=memory)
        key = (str(Path.cwd().resolve()), service._today().isoformat())
        service._sessions[key] = 'live'
        with self.assertRaisesRegex(RuntimeError, 'offline'):
            service.reset_session(Path.cwd())
        self.assertEqual(service._sessions[key], 'live')
        backend.archive.assert_not_called()
        memory.reset_session.assert_not_called()
        self.assertFalse(service._active.locked())

    def test_saved_session_archived_before_pointer_removed(self):
        calls = Mock()
        calls.memory.session.return_value = 'saved'
        calls.memory.compaction_revision.return_value = (1, 0)
        reset_saved_session(calls.backend, calls.memory, 'codex', '/work', '2026-10-31')
        self.assertEqual([c[0] for c in calls.mock_calls],
                         ['memory.session', 'memory.compaction_revision', 'backend.compact',
                          'memory.mark_compacted', 'backend.archive', 'memory.reset_session'])
        calls.backend.archive.assert_called_once_with('saved')

    def test_archive_failure_preserves_live_and_saved_pointer_and_unlocks(self):
        backend, memory = Mock(), Mock()
        memory.compaction_revision.return_value = (0, 0)
        backend.archive.side_effect = RuntimeError('offline')
        service = Orchestrator(backend, Mock(), Mock(), Mock(), Mock(), durable=memory)
        key = (str(Path.cwd().resolve()), service._today().isoformat())
        service._sessions[key] = 'live'
        with self.assertRaisesRegex(RuntimeError, 'offline'):
            service.reset_session(Path.cwd())
        self.assertEqual(service._sessions[key], 'live')
        memory.reset_session.assert_not_called()
        self.assertFalse(service._active.locked())

    def test_empty_session_does_not_archive(self):
        backend = Mock()
        reset_saved_session(backend, None, 'codex', '/work', '2026-10-31')
        backend.archive.assert_not_called()

    def test_history_off_resets_only_live_session(self):
        backend, memory = Mock(), Mock()
        service = Orchestrator(backend, Mock(), Mock(), Mock(), Mock(),
                               durable=memory, resume_history=lambda: False)
        key = (str(Path.cwd().resolve()), service._today().isoformat())
        service._sessions[key] = 'private'
        service.reset_session(Path.cwd())
        backend.archive.assert_called_once_with('private')
        self.assertFalse(service._sessions)
        self.assertFalse(memory.mock_calls)
