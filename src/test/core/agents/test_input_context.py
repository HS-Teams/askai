import unittest
from unittest.mock import patch
from askai.core.agents.input_context import prepared_input, MAX_INPUT_CHARS
from askai.core.agents.contracts import AgentError


class InputContextTests(unittest.TestCase):
    def test_small_request_is_unchanged(self):
        with prepared_input("liste meus downloads") as text:
            self.assertEqual(text, "liste meus downloads")

    def test_large_request_is_rejected_without_creating_context_files(self):
        with self.assertRaises(AgentError):
            with prepared_input("x" * (MAX_INPUT_CHARS + 1)):
                self.fail("oversized input accepted")

    def test_token_budget_is_checked(self):
        with patch.dict("os.environ", {"ASKAI_CONTEXT_BUDGET": "1024"}):
            with self.assertRaises(AgentError):
                with prepared_input("word " * 3000):
                    self.fail("token budget exceeded")
