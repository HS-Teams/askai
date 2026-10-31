"""Search formatting uses the existing refinement call and final-answer contract."""
import json
from pathlib import Path
import unittest
from unittest.mock import Mock

from askai.core.component.answer_refiner import refine_response
from askai.core.component.search_presentation import CATEGORY_ICONS, search_refinement_instructions
from askai.exception.exceptions import InaccurateResponse

PROMPTS = Path(__file__).parents[3] / 'main/askai/resources/prompts'


class SearchRefinementTests(unittest.TestCase):
    def refine(self, payload):
        model = Mock()
        model.complete.return_value = json.dumps(payload)
        answer = refine_response(
            model, (PROMPTS / 'taius/taius-session-refiner.txt').read_text(),
            user='Hjunior', locale='pt_BR',
            search_instructions=search_refinement_instructions('pt_BR'),
        )
        return model, answer

    def test_original_prompt_and_categories_reach_single_refinement_call(self):
        expected = '1. **[Projeto](https://example.org)**: descrição.\n\n---\n\n` Programação`  **Fontes:** [Projeto](https://example.org)\n\n>  Termos: projeto'
        model, answer = self.refine({'final_answer': expected})
        self.assertEqual(expected, answer)
        model.complete.assert_called_once()
        instructions = model.complete.call_args.args[0][0]['content']
        self.assertIn('You are an Internet Search Refinement Agent.', instructions)
        self.assertIn('pt_BR', instructions)
        for name, icon in CATEGORY_ICONS.items():
            self.assertIn(f'{name}: {icon}', instructions)
        for placeholder in ('{context}', '{question}', '{datetime}', '{search_instructions}'):
            self.assertNotIn(placeholder, instructions)

    def test_ordinary_answer_is_preserved_without_forcing_search_footer(self):
        model, answer = self.refine({'final_answer': 'Bom dia! {Tudo bem?}'})
        self.assertEqual('Bom dia! {Tudo bem?}', answer)
        self.assertIn('never to greetings, local actions or RAG-only answers', model.complete.call_args.args[0][0]['content'])

    def test_refinement_report_is_still_rejected(self):
        with self.assertRaises(InaccurateResponse):
            self.refine({'final_answer': 'Resultado', 'reasoning': 'Refinement report'})
