import json
import sys
import unittest
from threading import Event
from unittest.mock import Mock, patch
from askai.core.agents.camera_tool import capture_camera


class HostCameraTests(unittest.TestCase):
    def test_consent_precedes_capture_and_preserves_actual_path(self):
        camera = Mock()
        camera.capture_frame.return_value = '/photos/original-PHOTO.jpg'
        emit = Mock()
        with patch.dict(sys.modules, {'askai.core.component.multimedia.camera': Mock(camera=camera)}):
            result = capture_camera({'threadId': 's', 'turnId': 't', 'arguments': {}},
                                    Mock(return_value={'action': 'accept', 'content': {}}), emit, Event())
        self.assertEqual(json.loads(result['contentItems'][0]['text'])['target'], '/photos/original-PHOTO.jpg')
        camera.capture_frame.assert_called_once()
        self.assertEqual([c.args[0].kind for c in emit.call_args_list], ['camera_started', 'camera_finished'])

    def test_decline_and_cancel_do_not_touch_camera(self):
        for action in ('decline', 'cancel'):
            module = Mock()
            with patch.dict(sys.modules, {'askai.core.component.multimedia.camera': module}):
                result = capture_camera({'arguments': {}}, Mock(return_value={'action': action}), Mock(), Event())
            module.camera.capture_frame.assert_not_called()
            self.assertEqual(json.loads(result['contentItems'][0]['text'])['status'], 'cancelled')

    def test_failure_resumes_presentation_without_claiming_capture(self):
        camera = Mock()
        camera.capture_frame.side_effect = RuntimeError('camera unavailable')
        emit = Mock()
        with patch.dict(sys.modules, {'askai.core.component.multimedia.camera': Mock(camera=camera)}):
            with self.assertRaises(RuntimeError):
                capture_camera({'threadId': 's', 'turnId': 't', 'arguments': {}},
                               Mock(return_value={'action': 'accept', 'content': {}}), emit, Event())
        self.assertEqual(emit.call_args.args[0].kind, 'camera_finished')

class CameraDispatchTests(unittest.TestCase):
    def test_host_tool_dispatch_and_read_only_denial(self):
        from askai.core.agents.codex import CodexBackend
        for allowed in (True, False):
            with self.subTest(allowed=allowed):
                transport = Mock()
                transport.receive.side_effect = [
                    {'id': 7, 'method': 'item/tool/call', 'params': {'tool': 'capture_camera', 'arguments': {}, 'threadId': 's', 'turnId': 't'}},
                    {'method': 'item/completed', 'params': {'item': {'id': 'a', 'type': 'agentMessage', 'phase': 'final_answer', 'text': 'Done'}}},
                    {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
                ]
                with patch('askai.core.agents.codex.capture_camera', return_value={'success': True, 'contentItems': []}) as capture:
                    CodexBackend()._consume(transport, 's', 't', Mock(), Mock(), Event(), allow_tools=allowed)
                self.assertEqual(capture.call_count, int(allowed))
                self.assertEqual(transport.send.call_args.args[0]['result']['success'], allowed)
