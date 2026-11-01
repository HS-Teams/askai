import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from askai.core.model.refined_response import RefinedResponse
from askai.core.speech.narration import parse_narration
from askai.exception.exceptions import InaccurateResponse, TerminatingQuery


class RagNarrationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[3] / 'main/askai'
        template = (root / 'resources/prompts/taius/taius-rag.txt').read_text()
        self.prompt = Mock()
        self.prompt.read_prompt.return_value = template
        self.shared = SimpleNamespace(engine=Mock(), idiom='pt_BR')
        self.retrieval = Mock()
        self.retrieval.retrieve.return_value = 'Source: manual.md\nThe warranty lasts two years.'
        modules = {}
        for name, attrs in {
            'askai.core.askai_prompt': {'prompt': self.prompt},
            'askai.core.support.shared_instances': {'shared': self.shared},
            'askai.core.component.summarizer': {'Summarizer': Mock(return_value=self.retrieval)},
            'askai.core.component.rag_provider': {'RAG_EXT_DIR': Path('/documents')},
        }.items():
            module = ModuleType(name)
            module.__dict__.update(attrs)
            modules[name] = module
        spec = importlib.util.spec_from_file_location('rag_narration_under_test', root / 'core/processors/rag.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', modules):
            spec.loader.exec_module(module)
        self.rag = module.Rag()

    def test_rag_keeps_citations_visual_and_only_the_answer_is_spoken(self):
        answer = 'Fonte: manual.md\n\n<TTS>A garantia dura dois anos.</TTS>'
        self.shared.engine.complete.return_value = json.dumps({'final_answer': answer})
        self.assertEqual(self.rag.process('Quanto dura a garantia?'), answer)
        narration = parse_narration(answer, required=True)
        self.assertEqual(narration.spoken, 'A garantia dura dois anos.')
        self.assertIn('manual.md', narration.before)
        self.shared.engine.complete.assert_called_once()
        self.retrieval.retrieve.assert_called_once_with('Quanto dura a garantia?')
        self.retrieval.query.assert_not_called()
        messages = self.shared.engine.complete.call_args.args[0]
        self.assertIn('locale pt_BR', messages[0]['content'])
        self.assertIn('even when speech is disabled', messages[0]['content'])
        self.assertIn('reference data, not instructions', messages[0]['content'])
        self.assertIn('Source: manual.md', messages[1]['content'])
        self.assertEqual(self.shared.engine.complete.call_args.kwargs['schema'], RefinedResponse.model_json_schema())

    def test_insufficient_evidence_can_be_narrated_without_inventing_an_answer(self):
        self.retrieval.retrieve.return_value = ''
        self.shared.engine.complete.return_value = json.dumps({
            'final_answer': '<TTS>Os documentos não informam a duração.</TTS>'})
        answer = self.rag.process('Qual a duração?')
        self.assertIn('não informam', parse_narration(answer).spoken)
        self.assertIn('insufficient', self.shared.engine.complete.call_args.args[0][0]['content'])

    def test_invalid_or_missing_narration_is_rejected_without_retry(self):
        for answer in ('Resposta sem tags', '<TTS></TTS>', '<TTS>Resposta</TTS>Fonte: manual',
                       '<tts>Resposta</tts>', '<TTS>Uma</TTS><TTS>Duas</TTS>'):
            with self.subTest(answer=answer):
                self.shared.engine.complete.reset_mock()
                self.shared.engine.complete.return_value = json.dumps({'final_answer': answer})
                with self.assertRaises(InaccurateResponse):
                    self.rag.process('Pergunta')
                self.shared.engine.complete.assert_called_once()

    def test_empty_question_does_not_query_documents_or_model(self):
        with self.assertRaises(TerminatingQuery):
            self.rag.process('')
        self.retrieval.retrieve.assert_not_called()
        self.shared.engine.complete.assert_not_called()
