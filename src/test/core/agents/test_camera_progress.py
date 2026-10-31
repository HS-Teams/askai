import unittest
from threading import Event
from unittest.mock import Mock

from askai.core.agents.codex import CodexBackend


class CameraProgressTests(unittest.TestCase):
    def test_mcp_countdown_is_forwarded_without_becoming_answer(self):
        transport = Mock()
        transport.receive.side_effect = [
            {'method': 'item/mcpToolCall/progress', 'params': {'threadId': 's', 'turnId': 't', 'itemId': 'camera', 'message': 'Camera: 3'}},
            {'method': 'item/completed', 'params': {'item': {'type': 'agentMessage', 'phase': 'final_answer', 'id': 'a', 'text': 'Photo description'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ]
        emit = Mock()
        result = CodexBackend()._consume(transport, 's', 't', emit, Mock(), Event())
        self.assertEqual(result.answer, 'Photo description')
        progress = emit.call_args_list[0].args[0]
        self.assertEqual(progress.kind, 'tool_progress')
        self.assertEqual(progress.data['message'], 'Camera: 3')
