import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from askai.core.model.refined_response import RefinedResponse
from askai.core.speech.narration import parse_narration
from askai.exception.exceptions import InaccurateResponse


class ChatNarrationTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[3] / 'main/askai'
        self.template = (root / 'resources/prompts/taius/taius-jarvis.txt').read_text()
        self.prompt = Mock(user='hjunior')
        self.prompt.read_prompt.return_value = self.template
        self.shared = SimpleNamespace(engine=Mock(), idiom='pt_BR', context=Mock())
        self.shared.context.messages.return_value = []
        modules = {}
        for name, attrs in {
            'askai.core.askai_prompt': {'prompt': self.prompt},
            'askai.core.support.shared_instances': {'shared': self.shared},
        }.items():
            module = ModuleType(name)
            module.__dict__.update(attrs)
            modules[name] = module
        spec = importlib.util.spec_from_file_location('chat_narration_under_test', root / 'core/processors/chat.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict('sys.modules', modules):
            spec.loader.exec_module(module)
        self.chat = module.ChatProcessor()

    def test_chat_generates_valid_narration_in_one_structured_inference(self):
        answer = 'Detalhes visuais.\n\n<TTS>[happy]Olá, Hjunior!</TTS>'
        self.shared.engine.complete.return_value = json.dumps({'final_answer': answer})
        self.assertEqual(self.chat.process('oi', context='reference data'), answer)
        self.shared.engine.complete.assert_called_once()
        messages = self.shared.engine.complete.call_args.args[0]
        self.assertEqual(self.shared.engine.complete.call_args.kwargs['schema'], RefinedResponse.model_json_schema())
        self.assertIn('<TTS>...</TTS>', messages[0]['content'])
        self.assertIn('even when speech is disabled', messages[0]['content'])
        self.assertIn('reference data', messages[0]['content'])
        self.assertEqual(messages[-1], {'role': 'user', 'content': 'oi'})
        self.assertEqual(parse_narration(answer).spoken, '[happy]Olá, Hjunior!')

    def test_chat_rejects_missing_empty_or_misplaced_narration(self):
        for answer in ('Hello', '<TTS></TTS>', '<TTS>Hello</TTS>more', '<tts>Hello</tts>',
                       '<TTS>One</TTS><TTS>Two</TTS>'):
            with self.subTest(answer=answer):
                self.shared.engine.complete.return_value = json.dumps({'final_answer': answer})
                with self.assertRaises(InaccurateResponse):
                    self.chat.process('hi')

    def test_chat_preserves_history_without_repeating_the_latest_question(self):
        self.shared.context.messages.return_value = [{'role': 'user', 'content': 'oi'}]
        self.shared.engine.complete.return_value = '{"final_answer":"<TTS>Olá!</TTS>"}'
        self.chat.process('oi')
        messages = self.shared.engine.complete.call_args.args[0]
        self.assertEqual(sum(message == {'role': 'user', 'content': 'oi'} for message in messages), 1)

    def test_chat_rejects_invalid_structured_output_without_retrying(self):
        for raw in ('<TTS>Olá!</TTS>', '{broken', '{}'):
            with self.subTest(raw=raw):
                self.shared.engine.complete.reset_mock()
                self.shared.engine.complete.return_value = raw
                with self.assertRaises(InaccurateResponse):
                    self.chat.process('oi')
                self.shared.engine.complete.assert_called_once()
