import json
import sys
import unittest
from threading import Event
from unittest.mock import Mock, patch
from askai.core.agents.screenshot_tool import capture_screenshot


class ScreenshotToolTests(unittest.TestCase):
    def test_accept_captures_and_returns_path_for_agent_analysis(self):
        module = Mock()
        module.capture_screenshot.return_value = '/askai/cache/screenshots/test.jpeg'
        emit = Mock()
        with patch.dict(sys.modules, {'askai.core.component.multimedia.screenshot': module}):
            result = capture_screenshot({'arguments': {}, 'threadId': 's', 'turnId': 't'},
                Mock(return_value={'action': 'accept', 'content': {}}), emit, Event())
        body = json.loads(result['contentItems'][0]['text'])
        self.assertEqual(body['status'], 'completed')
        self.assertEqual(body['target'], '/askai/cache/screenshots/test.jpeg')
        module.capture_screenshot.assert_called_once()
        self.assertEqual([c.args[0].kind for c in emit.call_args_list], ['screenshot_started', 'screenshot_finished'])

    def test_decline_or_cancel_never_captures(self):
        for action in ('decline', 'cancel'):
            module = Mock()
            with patch.dict(sys.modules, {'askai.core.component.multimedia.screenshot': module}):
                result = capture_screenshot({'arguments': {}}, Mock(return_value={'action': action}), Mock(), Event())
            module.capture_screenshot.assert_not_called()
            self.assertEqual(json.loads(result['contentItems'][0]['text'])['status'], 'cancelled')

    def test_capture_error_is_not_a_successful_image(self):
        module = Mock()
        module.capture_screenshot.side_effect = RuntimeError('screen permission denied')
        emit = Mock()
        with patch.dict(sys.modules, {'askai.core.component.multimedia.screenshot': module}):
            with self.assertRaises(RuntimeError):
                capture_screenshot({'arguments': {}, 'threadId': 's', 'turnId': 't'},
                    Mock(return_value={'action': 'accept', 'content': {}}), emit, Event())
        self.assertEqual(emit.call_args.args[0].kind, 'screenshot_finished')

    def test_dispatch_is_denied_during_read_only_review(self):
        from askai.core.agents.codex import CodexBackend
        for allow_tools in (True, False):
            transport = Mock()
            transport.receive.side_effect = [
                {'id': 9, 'method': 'item/tool/call', 'params': {'tool': 'capture_screenshot', 'arguments': {}, 'threadId': 's', 'turnId': 't'}},
                {'method': 'item/completed', 'params': {'item': {'id': 'a', 'type': 'agentMessage', 'phase': 'final_answer', 'text': 'Done'}}},
                {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
            ]
            with patch('askai.core.agents.codex.capture_screenshot', return_value={'success': True, 'contentItems': []}) as capture:
                CodexBackend()._consume(transport, 's', 't', Mock(), Mock(), Event(), allow_tools=allow_tools)
            self.assertEqual(capture.call_count, int(allow_tools))
            self.assertEqual(transport.send.call_args.args[0]['result']['success'], allow_tools)
