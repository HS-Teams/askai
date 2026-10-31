"""Regression coverage for absent and malformed task-splitter lists."""
import unittest
from unittest.mock import patch

from askai.core.model.action_plan import ActionPlan
from askai.core.model.model_result import ModelResult
from askai.core.support.llm_parser import parse_list
from askai.exception.exceptions import InaccurateResponse


class TestActionPlanLists(unittest.TestCase):
    def test_greeting_with_valid_empty_lists(self):
        response = (
            "@primary_goal: None.\n"
            "@sub_goals: []\n"
            "@speak: Hello, I'm Taius the Task Splitter, here to help you with your tasks.\n"
            "@tasks: []"
        )
        with patch("askai.core.model.action_plan.Path.write_text"):
            plan = ActionPlan.create("hello", response, ModelResult.default())
        self.assertTrue(plan.is_direct)
        self.assertEqual(plan.sub_goals, [])
        self.assertEqual(plan.tasks, [])
        self.assertIn("Hello", plan.speak)

    def test_non_json_absence_is_rejected(self):
        for value in ["None", "None.", "null", ""]:
            response = f"@sub_goals: {value}\n@speak: Hi\n@tasks: []"
            with self.subTest(value=value), patch("askai.core.model.action_plan.Path.write_text"):
                with self.assertRaises(InaccurateResponse):
                    ActionPlan.create("hello", response, ModelResult.default())

    def test_malformed_lists_raise_domain_error(self):
        for value in ['[oops]', '["not a task object"]', '[{"id": 1, "task": ]']:
            with self.subTest(value=value), patch("askai.core.model.action_plan.Path.write_text"):
                with self.assertRaises(InaccurateResponse):
                    ActionPlan.create("hello", f"@sub_goals: []\n@tasks: {value}", ModelResult.default())

    def test_json_objects_and_string_lists_keep_their_content(self):
        tasks = parse_list("@tasks", '@tasks: [{"id": 1, "task": "List files"}]')
        self.assertEqual(tasks[0].task, "List files")
        self.assertEqual(parse_list("@items", '@items: ["one", "two"]', is_dict=False), ["one", "two"])


if __name__ == "__main__":
    unittest.main()
