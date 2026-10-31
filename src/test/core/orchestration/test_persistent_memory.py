import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from askai.core.agents.contracts import AgentEvent, AgentResult
from askai.core.orchestration.orchestrator import Orchestrator
from askai.core.support.persistent_memory import PersistentMemory
from askai.core.support.short_term_memory import ShortTermMemory


class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "memory.sqlite3"
        self.cwd = Path(self.directory.name).resolve()

    def service(self, backend, validator=None, agent="codex"):
        return Orchestrator(
            backend,
            ShortTermMemory(2),
            lambda q: "",
            validator or Mock(),
            lambda q, a, r: a,
            durable=PersistentMemory(self.path),
            agent_name=agent,
        )

    def test_restart_resumes_session_and_keeps_stm_bounded(self):
        backend = Mock()
        backend.run.return_value = AgentResult(
            "session-1", "turn", "Created notes.txt", "completed"
        )
        first = self.service(backend)
        first.process("Create notes.txt", self.cwd, "", Mock(), Mock())
        second = self.service(backend)
        second.process("What did you do?", self.cwd, "", Mock(), Mock())
        task = backend.run.call_args.args[0]
        self.assertEqual(task.session_id, "session-1")
        self.assertNotIn("Created notes.txt", task.context)
        self.assertNotIn("Historical activity", task.context)
        self.assertEqual(len(second._memory.messages), 2)
        self.assertIsNone(PersistentMemory(self.path).session("claude", str(self.cwd)))
        self.assertIsNone(
            PersistentMemory(self.path).session("codex", str(self.cwd / "other"))
        )

    def test_observed_actions_and_decisions_survive_validation_failure(self):
        def run(task, emit, interact, cancel):
            emit(AgentEvent("started", "s", "t"))
            interact("approval", {"command": "touch notes.txt"})
            emit(AgentEvent("tool_completed", "s", "t", {"exitCode": 0}))
            return AgentResult("s", "t", "Created notes.txt", "completed")

        backend = Mock(run=Mock(side_effect=run))
        with self.assertRaises(ValueError):
            self.service(backend, Mock(side_effect=ValueError("invalid"))).process(
                "create",
                self.cwd,
                "",
                Mock(),
                Mock(return_value={"decision": "accept"}),
            )
        memory = PersistentMemory(self.path)
        history = memory.context("codex", str(self.cwd))
        for entry in ("decision", "tool_completed", "failed", "Created notes.txt"):
            self.assertIn(entry, history)
        self.assertEqual(memory.session("codex", str(self.cwd)), "s")
        backend.run.assert_called_once()

    def test_secret_answers_are_not_journaled(self):
        def run(task, emit, interact, cancel):
            interact("item/tool/requestUserInput", {"questions": [{"isSecret": True}]})
            raise RuntimeError("stopped")

        with self.assertRaises(RuntimeError):
            self.service(Mock(run=run)).process(
                "question",
                self.cwd,
                "",
                Mock(),
                Mock(return_value={"answer": "SECRET"}),
            )
        history = PersistentMemory(self.path).context("codex", str(self.cwd))
        self.assertNotIn("SECRET", history)
        self.assertIn("[private]", history)

    def test_incomplete_request_remains_visible_after_reopen(self):
        memory = PersistentMemory(self.path)
        memory.begin("codex", str(self.cwd), "unfinished objective")
        self.assertIn(
            "unfinished objective",
            PersistentMemory(self.path).context("codex", str(self.cwd)),
        )

    def test_daily_rotation_preserves_sessions_and_pins_date_during_execution(self):
        from datetime import date

        day = [date(2026, 10, 31)]
        backend = Mock()
        sequence = iter(["october", "october", "november"])

        def run(task, emit, interact, cancel):
            session = next(sequence)
            if task.instruction == "cross midnight":
                day[0] = date(2026, 11, 1)
            emit(AgentEvent("started", session, "turn"))
            return AgentResult(session, "turn", "Done", "completed")

        backend.run.side_effect = run
        service = Orchestrator(
            backend,
            ShortTermMemory(2),
            lambda q: "",
            Mock(),
            lambda q, a, r: a,
            durable=PersistentMemory(self.path),
            today=lambda: day[0],
        )
        service.process("first", self.cwd, "", Mock(), Mock())
        first = backend.run.call_args.args[0]
        self.assertIsNone(first.session_id)
        self.assertEqual(first.session_name, "2026-10-31")
        service.process("cross midnight", self.cwd, "", Mock(), Mock())
        self.assertEqual(backend.run.call_args.args[0].session_id, "october")
        service.process("new day", self.cwd, "", Mock(), Mock())
        latest = backend.run.call_args.args[0]
        self.assertIsNone(latest.session_id)
        self.assertEqual(latest.session_name, "2026-11-01")
        memory = PersistentMemory(self.path)
        self.assertEqual(
            memory.session("codex", str(self.cwd), "2026-10-31"), "october"
        )
        self.assertEqual(
            memory.session("codex", str(self.cwd), "2026-11-01"), "november"
        )

    def test_existing_undated_history_is_preserved(self):
        import sqlite3

        with sqlite3.connect(self.path) as db:
            db.execute(
                "CREATE TABLE sessions(agent TEXT, cwd TEXT, session TEXT, PRIMARY KEY(agent,cwd))"
            )
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?)",
                ("codex", str(self.cwd), "old-session"),
            )
        memory = PersistentMemory(self.path)
        self.assertIsNone(memory.session("codex", str(self.cwd), "2026-11-01"))
        with sqlite3.connect(self.path) as db:
            self.assertEqual(
                db.execute("SELECT session FROM sessions").fetchone()[0], "old-session"
            )

    def test_reset_starts_new_session_and_preserves_history_and_stm(self):
        backend = Mock()
        backend.run.return_value = AgentResult(
            "old", "t", "Previous answer", "completed"
        )
        service = self.service(backend)
        service.process("first", self.cwd, "", Mock(), Mock())
        previous_stm = service._memory.messages
        service.reset_session(self.cwd)
        self.assertEqual(service._memory.messages, previous_stm)
        memory = PersistentMemory(self.path)
        self.assertIsNone(memory.session("codex", str(self.cwd)))
        self.assertIn("Previous answer", memory.context("codex", str(self.cwd)))
        self.assertIn("previous_session", memory.context("codex", str(self.cwd)))
        backend.run.return_value = AgentResult("new", "t2", "New answer", "completed")
        service.process("second", self.cwd, "", Mock(), Mock())
        self.assertIsNone(backend.run.call_args.args[0].session_id)
        self.assertEqual(memory.session("codex", str(self.cwd)), "new")

    def test_reset_is_scoped_and_rejected_during_task(self):
        memory = PersistentMemory(self.path)
        memory.record(
            "codex",
            str(self.cwd),
            "r",
            "started",
            {},
            "yesterday",
            session_date="2000-01-01",
        )
        service = self.service(Mock())
        service._active.acquire()
        try:
            with self.assertRaisesRegex(RuntimeError, "Wait for"):
                service.reset_session(self.cwd)
        finally:
            service._active.release()
        service.reset_session(self.cwd)
        self.assertEqual(
            memory.session("codex", str(self.cwd), "2000-01-01"), "yesterday"
        )

    def test_history_off_skips_restart_resume_but_keeps_live_session(self):
        backend = Mock()
        backend.run.return_value = AgentResult("previous", "t", "Old answer", "completed")
        self.service(backend).process("old", self.cwd, "", Mock(), Mock())
        restarted = self.service(backend)
        enabled = [False]
        restarted._resume_history = lambda: enabled[0]
        backend.run.return_value = AgentResult("current", "t2", "New answer", "completed")
        restarted.process("new", self.cwd, "", Mock(), Mock())
        self.assertIsNone(backend.run.call_args.args[0].session_id)
        restarted.process("continue", self.cwd, "", Mock(), Mock())
        self.assertEqual(backend.run.call_args.args[0].session_id, "current")
        enabled[0] = True
        restarted.process("still here", self.cwd, "", Mock(), Mock())
        self.assertEqual(backend.run.call_args.args[0].session_id, "previous")
        self.service(backend).process("resume enabled", self.cwd, "", Mock(), Mock())
        self.assertEqual(backend.run.call_args.args[0].session_id, "current")
        entries = PersistentMemory(self.path).conversations("codex", str(self.cwd))
        self.assertEqual(entries[0]["session"], "previous")
        self.assertEqual(entries[1]["session"], "current")

    def test_conversations_keep_session_identity_after_reset_and_filter_scope(self):
        from datetime import date
        backend = Mock()
        backend.run.return_value = AgentResult("first", "t", "First answer", "completed")
        service = self.service(backend)
        service.process("first question", self.cwd, "", Mock(), Mock())
        service.reset_session(self.cwd)
        backend.run.return_value = AgentResult("second", "t", "Second answer", "completed")
        service.process("second question", self.cwd, "", Mock(), Mock())
        memory = PersistentMemory(self.path)
        entries = memory.conversations("codex", str(self.cwd), date.today().isoformat())
        self.assertEqual([e["session"] for e in entries], ["first", "second"])
        self.assertEqual([e["answer"] for e in entries], ["First answer", "Second answer"])
        self.assertEqual(memory.conversations("claude", str(self.cwd)), [])
        self.assertEqual(memory.conversations("codex", str(self.cwd / "other")), [])
        self.assertEqual(memory.conversations("codex", str(self.cwd), "2000-01-01"), [])
        with self.assertRaises(ValueError):
            memory.conversations("codex", str(self.cwd), "invalid")

    def test_history_does_not_turn_failed_or_incomplete_requests_into_answers(self):
        memory = PersistentMemory(self.path)
        failed = memory.begin("codex", str(self.cwd), "failed question", day="2026-10-31")
        memory.record("codex", str(self.cwd), failed, "started", {}, "s", "2026-10-31")
        memory.record("codex", str(self.cwd), failed, "failed", {"error": "validation failed"})
        memory.begin("codex", str(self.cwd), "unfinished", day="2026-10-31")
        entries = memory.conversations("codex", str(self.cwd), "2026-10-31")
        self.assertEqual(entries[0]["session"], "s")
        self.assertEqual(entries[0]["error"], "validation failed")
        self.assertIsNone(entries[0]["answer"])
        self.assertIsNone(entries[1]["answer"])
        self.assertIsNone(entries[1]["session"])

    def test_history_off_does_not_record_actions_decisions_answers_or_failures(self):
        def run(task, emit, interact, cancel):
            self.assertFalse(task.persist_history)
            emit(AgentEvent('started', 'private', 't'))
            interact('approval', {'command': 'example'})
            emit(AgentEvent('tool_completed', 'private', 't', {'exitCode': 0}))
            return AgentResult('private', 't', 'private answer', 'completed')
        backend = Mock(run=Mock(side_effect=run))
        service = self.service(backend)
        service._resume_history = lambda: False
        service.process('private question', self.cwd, '', Mock(), Mock(return_value={'decision': 'accept'}))
        self.assertEqual(PersistentMemory(self.path).conversations('codex', str(self.cwd)), [])
        self.assertTrue(service._memory.messages)
        self.assertTrue(all(not message.recordable for message in service._memory.messages))
        backend.run.side_effect = RuntimeError('private failure')
        with self.assertRaises(RuntimeError):
            service.process('another private question', self.cwd, '', Mock(), Mock())
        self.assertEqual(PersistentMemory(self.path).conversations('codex', str(self.cwd)), [])
