import json
from pathlib import Path
import unittest
from unittest.mock import patch
from askai.core.agents.contracts import AgentResult
from askai.core.engine.agent.agent_engine import AgentEngine
from askai.core.component.answer_validator import validate_response
from askai.core.component.answer_refiner import refine_response

PROMPTS = Path(__file__).parents[3] / 'main/askai/resources/prompts/taius'

class SessionReviewTests(unittest.TestCase):
    def test_reviews_reference_execution_turn_without_fake_answer_or_history(self):
        with patch('askai.core.engine.agent.agent_engine.create_backend') as factory:
            backend = factory.return_value
            backend.run.side_effect = [
                AgentResult('s', 'validation-turn', json.dumps(dict(color='Blue', accuracy=100.0, reasoning='Supported', tips='')), 'completed'),
                AgentResult('s', 'refiner-turn', json.dumps(dict(final_answer='<TTS>Encontrei cinco pastas.</TTS>')), 'completed'),
            ]
            engine = AgentEngine('codex')
            with engine.use_session('s'):
                validate_response(engine, (PROMPTS / 'taius-session-validator.txt').read_text())
                answer = refine_response(engine, (PROMPTS / 'taius-session-refiner.txt').read_text(), user='Hjunior', locale='pt_BR')
            self.assertEqual(answer, '<TTS>Encontrei cinco pastas.</TTS>')
            expected_messages = [
                {'role': 'user', 'content': (PROMPTS / 'taius-session-validator.txt').read_text().format()},
                {'role': 'system', 'content': (PROMPTS / 'taius-session-refiner.txt').read_text().format(
                    user='Hjunior', locale='pt_BR', assistive_instructions='', search_instructions='')},
            ]
            for call, expected in zip(backend.run.call_args_list, expected_messages, strict=True):
                task = call.args[0]
                self.assertEqual(task.session_id, 's')
                self.assertIn('most recent task answer', task.instruction)
                self.assertNotIn('AI Response:', task.instruction)
                messages = json.loads(task.instruction.split('task messages:\n', 1)[1])
                self.assertEqual(messages, [expected])
