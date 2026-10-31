import json
import unittest
from unittest.mock import Mock, patch
from askai.core.agents.contracts import AgentResult, AgentError
from askai.core.agents.factory import create_backend, normalize_agent
from askai.core.engine.agent.agent_engine import AgentEngine


class AgentEngineTests(unittest.TestCase):
    def test_names_are_case_insensitive_and_old_engines_are_rejected(self):
        for name in ("Codex", "codex", "CODEX"):
            self.assertEqual(normalize_agent(name), "codex")
        with self.assertRaises(AgentError):
            normalize_agent("llama")
        for name in ("Claude", "Cursor"):
            with self.assertRaisesRegex(AgentError, "not implemented"):
                create_backend(name)

    def test_quality_inference_uses_selected_agent_schema_and_model(self):
        with patch("askai.core.engine.agent.agent_engine.create_backend") as factory:
            backend = factory.return_value
            backend.run.return_value = AgentResult(
                "s", "t", '{"final_answer":"Hi"}', "completed"
            )
            engine = AgentEngine("Codex", "selected-model")
            schema = {"type": "object"}
            result = engine.complete(
                [{"role": "user", "content": "Refine"}], schema=schema
            )
        self.assertEqual(json.loads(result), {"final_answer": "Hi"})
        task = backend.run.call_args.args[0]
        self.assertEqual(task.model, "selected-model")
        self.assertEqual(task.output_schema, schema)
        self.assertTrue(task.read_only)
        self.assertIn("Refine", task.instruction)

    def test_no_model_override_uses_runtime_default(self):
        engine = AgentEngine("Codex")
        self.assertIsNone(engine.model)
        self.assertEqual(engine.nickname(), "Codex")
        self.assertEqual(engine.embedding_key(), "local:onnx:all-MiniLM-L6-v2")

    def test_interrupted_quality_inference_is_not_returned(self):
        with patch("askai.core.engine.agent.agent_engine.create_backend") as factory:
            factory.return_value.run.return_value = AgentResult(
                "s", "t", "", "interrupted"
            )
            with self.assertRaisesRegex(AgentError, "interrupted"):
                AgentEngine("codex").complete([])

    def test_reviews_reuse_execution_session_and_release_it_afterward(self):
        with patch("askai.core.engine.agent.agent_engine.create_backend") as factory:
            backend = factory.return_value
            backend.run.return_value = AgentResult(
                "session", "turn", "answer", "completed"
            )
            engine = AgentEngine("codex")
            with engine.use_session("execution-session"):
                engine.complete(
                    [{"role": "user", "content": "Validate previous answer"}]
                )
                self.assertEqual(
                    backend.run.call_args.args[0].session_id, "execution-session"
                )
                engine.complete([{"role": "user", "content": "Refine previous answer"}])
                self.assertEqual(
                    backend.run.call_args.args[0].session_id, "execution-session"
                )
            engine.complete([])
            self.assertIsNone(backend.run.call_args.args[0].session_id)
