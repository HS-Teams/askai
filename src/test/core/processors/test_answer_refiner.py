"""The refiner publishes only a complete, validated final-answer payload."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from askai.core.model.refined_response import RefinedResponse
from askai.core.component.answer_refiner import refine_response
from askai.exception.exceptions import InaccurateResponse


class TestAnswerRefiner(unittest.TestCase):
    def setUp(self):
        self.model = Mock()
        self.template = (Path(__file__).parents[3] / 'main/askai/resources/prompts/taius/taius-refiner.txt').read_text()
        self.arguments = dict(locale="en_US", user="Hjunior", improvements="Be concise", context="", response="Hello!", question="Hi")

    def invoke(self, payload):
        self.model.complete.return_value = payload
        return refine_response(self.model, self.template, **self.arguments)

    def test_returns_only_final_answer(self):
        self.assertEqual(self.invoke(json.dumps({"final_answer": "Hello, Hjunior!"})), "Hello, Hjunior!")
        self.assertEqual(self.model.complete.call_args.kwargs["schema"], RefinedResponse.model_json_schema())
        messages = self.model.complete.call_args.args[0]
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn('exactly one required field: "final_answer"', messages[0]["content"])
        self.assertIn('Human Question: "Hi"', messages[0]["content"])

    def test_assistive_prompt_is_composed_with_persona_and_same_schema(self):
        assistive = (Path(__file__).parents[3] / 'main/askai/resources/prompts/taius/taius-tts.txt').read_text()
        self.model.complete.return_value = '{"final_answer":"Resumo acessível, Hjunior."}'
        answer = refine_response(
            self.model, self.template, assistive_instructions=assistive, **self.arguments
        )
        self.assertEqual(answer, "Resumo acessível, Hjunior.")
        instructions = self.model.complete.call_args.args[0][0]['content']
        self.assertIn(assistive, instructions)
        self.assertIn('demeanor of Jarvis', instructions)
        self.assertNotIn('{assistive_instructions}', instructions)
        self.assertEqual(self.model.complete.call_args.kwargs['schema'], RefinedResponse.model_json_schema())

    def test_normal_mode_does_not_apply_accessible_list_limit(self):
        self.invoke('{"final_answer":"Hello!"}')
        instructions = self.model.complete.call_args.args[0][0]['content']
        self.assertIn('demeanor of Jarvis', instructions)
        self.assertNotIn('at most five representative entries', instructions)

    def test_preserves_markdown_and_whitespace(self):
        answer = '\n# Title\n\n```python\nprint("hello")\n```\n\n[link](https://example.com)\n'
        self.assertEqual(self.invoke(json.dumps({"final_answer": answer})), answer)

    def test_unchanged_answer_obeys_same_contract(self):
        self.assertEqual(self.invoke('{"final_answer":"Hello!"}'), self.arguments["response"])

    def test_rejects_extra_fields_missing_field_and_invalid_values(self):
        for payload in [
            {"final_answer": "Hi", "reasoning": "I edited the text"}, {},
            {"final_answer": ""}, {"final_answer": " \n\t"},
            {"final_answer": None}, {"final_answer": 123}, {"final_answer": ["Hi"]},
        ]:
            with self.subTest(payload=payload), self.assertRaises(InaccurateResponse):
                self.invoke(json.dumps(payload))

    def test_rejects_prose_fences_trailing_text_and_partial_json(self):
        for payload in ['Hello!', '```json\n{"final_answer":"Hi"}\n```',
                        '{"final_answer":"Hi"} Explanation', '{"final_answer":"Hi"']:
            with self.subTest(payload=payload), self.assertRaises(InaccurateResponse):
                self.invoke(payload)

    def test_does_not_filter_user_content_by_keywords(self):
        answer = 'The document has a section titled "Reason for Refinement".'
        self.assertEqual(self.invoke(json.dumps({"final_answer": answer})), answer)

    def test_provider_errors_are_not_replaced_with_a_fallback_answer(self):
        self.model.complete.side_effect = RuntimeError("Unavailable")
        with self.assertRaisesRegex(RuntimeError, "Unavailable"):
            refine_response(self.model, self.template, **self.arguments)


if __name__ == '__main__':
    unittest.main()
