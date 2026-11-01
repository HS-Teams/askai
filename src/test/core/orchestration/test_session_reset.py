import unittest
from unittest.mock import Mock
from pathlib import Path
from askai.core.orchestration.session_reset import reset_saved_session
from askai.core.orchestration.orchestrator import Orchestrator


class SessionResetTests(unittest.TestCase):
    def test_saved_session_archived_before_pointer_removed(self):
        calls = Mock()
        calls.memory.session.return_value = 'saved'
        reset_saved_session(calls.backend, calls.memory, 'codex', '/work', '2026-10-31')
        self.assertEqual([c[0] for c in calls.mock_calls],
                         ['memory.session', 'backend.archive', 'memory.reset_session'])
        calls.backend.archive.assert_called_once_with('saved')

    def test_archive_failure_preserves_live_and_saved_pointer_and_unlocks(self):
        backend, memory = Mock(), Mock()
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
