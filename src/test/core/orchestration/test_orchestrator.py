import unittest
from pathlib import Path
from unittest.mock import Mock
from askai.core.agents.contracts import AgentError, AgentResult
from askai.core.orchestration.orchestrator import Orchestrator
from askai.core.support.short_term_memory import ShortTermMemory


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.run.return_value = AgentResult(
            "s", "t", "Codex answer", "completed"
        )
        self.rag = Mock(return_value="")
        self.validator = Mock(return_value="assessment")
        self.refiner = Mock(return_value="Final answer")
        self.memory = ShortTermMemory(2)
        self.service = Orchestrator(
            self.backend, self.memory, self.rag, self.validator, self.refiner
        )

    def run_request(self, question="Original request"):
        return self.service.process(question, Path.cwd(), "context", Mock(), Mock())

    def test_every_question_reaches_codex_then_validation_then_refiner(self):
        for question in [
            "oi tudo bem?",
            "liste meus downloads",
            "como listar arquivos?",
        ]:
            with self.subTest(question=question):
                calls = Mock()
                calls.attach_mock(self.backend.run, "codex")
                calls.attach_mock(self.validator, "validate")
                calls.attach_mock(self.refiner, "refine")
                self.assertEqual(self.run_request(question), "Final answer")
                self.assertEqual(
                    [c[0] for c in calls.mock_calls], ["codex", "validate", "refine"]
                )
                self.assertEqual(
                    self.backend.run.call_args.args[0].instruction, question
                )
                self.assertEqual(self.memory.messages[-1].content, "Final answer")
                self.assertFalse(self.memory.pending)

    def test_rag_context_and_tool_evidence_reach_their_consumers(self):
        self.rag.return_value = "Retrieved source"
        evidence = (
            {
                "type": "commandExecution",
                "exitCode": 0,
                "aggregatedOutput": "invoice.pdf",
            },
        )
        self.backend.run.return_value = AgentResult(
            "s", "t", "invoice.pdf", "completed", evidence
        )
        self.run_request("liste meus downloads")
        self.assertIn("Retrieved source", self.backend.run.call_args.args[0].context)
        self.validator.assert_called_once_with(
            "liste meus downloads", "invoice.pdf", evidence
        )
        self.refiner.assert_called_once_with(
            "liste meus downloads", "invoice.pdf", "assessment"
        )

    def test_validation_failure_prevents_refinement_and_publication_without_retry(self):
        self.validator.side_effect = ValueError("Evidence missing")
        with self.assertRaisesRegex(ValueError, "Evidence missing"):
            self.run_request()
        self.backend.run.assert_called_once()
        self.refiner.assert_not_called()
        self.assertEqual(self.memory.pending["objective"], "Original request")
        self.assertFalse(any(m.role == "assistant" for m in self.memory.messages))

    def test_cancelled_execution_does_not_validate_or_refine(self):
        self.backend.run.return_value = AgentResult("s", "t", "", "interrupted")
        with self.assertRaisesRegex(AgentError, "cancelled"):
            self.run_request()
        self.validator.assert_not_called()
        self.refiner.assert_not_called()

    def test_session_is_resumed_only_in_same_directory(self):
        self.run_request()
        self.run_request()
        self.assertEqual(self.backend.run.call_args.args[0].session_id, "s")

    def test_pending_work_survives_message_eviction(self):
        self.memory.pending["task"] = "unfinished"
        for text in ["one", "two", "three"]:
            self.memory.add("human", text)
        self.assertEqual([m.content for m in self.memory.messages], ["two", "three"])
        self.assertEqual(self.memory.pending["task"], "unfinished")

    def test_concurrent_request_is_rejected(self):
        self.service._active.acquire()
        try:
            with self.assertRaisesRegex(AgentError, "already processing"):
                self.run_request()
            self.backend.run.assert_not_called()
        finally:
            self.service._active.release()

    def test_progress_covers_stages_and_always_finishes(self):
        for failure in (False, True):
            with self.subTest(failure=failure):
                events = []
                self.validator.side_effect = ValueError('invalid') if failure else None
                if failure:
                    with self.assertRaises(ValueError):
                        self.service.process('question', Path.cwd(), '', events.append, Mock())
                else:
                    self.service.process('question', Path.cwd(), '', events.append, Mock())
                stages = [event.data['stage'] for event in events if event.kind == 'stage']
                expected = ['retrieval', 'execution', 'validation']
                if not failure:
                    expected.append('refinement')
                self.assertEqual(stages, expected)
                self.assertEqual(events[-1].kind, 'finished')

    def test_connection_preparation_overlaps_retrieval_before_execution(self):
        from threading import Event
        connected, retrieved = Event(), Event()
        def prepare():
            connected.set()
            self.assertTrue(retrieved.wait(2))
        def retrieve(question):
            self.assertTrue(connected.wait(2))
            retrieved.set()
            return 'Source'
        self.service._prepare = prepare
        self.service._retrieve = retrieve
        self.run_request()
        self.assertIn('Source', self.backend.run.call_args.args[0].context)
        self.validator.assert_called_once()
        self.refiner.assert_called_once()

    def test_failed_connection_preparation_does_not_execute_or_review(self):
        self.service._prepare = Mock(side_effect=AgentError('Cannot connect'))
        with self.assertRaisesRegex(AgentError, 'Cannot connect'):
            self.run_request()
        self.backend.run.assert_not_called()
        self.validator.assert_not_called()
        self.refiner.assert_not_called()
