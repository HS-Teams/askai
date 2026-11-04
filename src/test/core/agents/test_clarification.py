import json
from threading import Event
import unittest
from unittest.mock import Mock, patch
from jsonschema import ValidationError
from askai.core.agents.clarification import clarify, USER_INPUT_METHOD
from askai.core.agents.codex import CodexBackend


class ClarificationTests(unittest.TestCase):
    def test_answers_return_in_same_tool_call(self):
        arguments = {'questions': [{'id': 'q', 'question': 'Where?'}]}
        response = {'answers': {'q': {'answers': ['Downloads']}}}
        interact = Mock(return_value=response)
        result = clarify({'arguments': arguments}, interact, Mock(), Event())
        interact.assert_called_once_with(USER_INPUT_METHOD, arguments)
        self.assertEqual(json.loads(result['contentItems'][0]['text']), response)

    def test_cancelled_task_never_prompts(self):
        cancelled = Event()
        cancelled.set()
        interact = Mock()
        result = clarify({'arguments': {'questions': [{'id': 'q', 'question': 'Where?'}]}},
                         interact, Mock(), cancelled)
        interact.assert_not_called()
        self.assertEqual(json.loads(result['contentItems'][0]['text']), {'answers': {}})

    def test_invalid_and_duplicate_questions_are_rejected_before_prompting(self):
        for questions in ([], [{'id': 'q', 'question': 'Where?'}] * 2):
            interact = Mock()
            with self.assertRaises((ValueError, ValidationError)):
                clarify({'arguments': {'questions': questions}}, interact, Mock(), Event())
            interact.assert_not_called()

    def test_long_user_wait_resumes_same_turn_without_replaying(self):
        now = [0.0]
        transport = Mock()
        transport.receive.side_effect = [
            {'id': 9, 'method': 'item/tool/call', 'params': {
                'threadId': 's', 'turnId': 't', 'tool': 'askai_clarify',
                'arguments': {'questions': [{'id': 'q', 'question': 'Where?'}]}}},
            {'method': 'item/completed', 'params': {'item': {
                'type': 'agentMessage', 'phase': 'final_answer', 'id': 'a', 'text': 'Done'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ]
        def answer(*_):
            now[0] += 3600
            return {'answers': {'q': {'answers': ['Downloads']}}}
        with patch('askai.core.agents.codex.monotonic', side_effect=lambda: now[0]):
            result = CodexBackend(timeout=10)._consume(
                transport, 's', 't', Mock(), answer, Event(), allow_tools=True)
        self.assertEqual((result.session_id, result.answer), ('s', 'Done'))
        transport.request.assert_not_called()
        self.assertEqual(transport.send.call_args.args[0]['id'], 9)
