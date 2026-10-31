import json
import sys
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch, AsyncMock

from askai.core.permissions.grants import GrantPolicy, GrantDenied
from askai.core.agents.camera_tool import capture_camera
from askai.core.agents.enrollment_tool import register_identities
from askai.mcp_server import create_server
from askai.core.capabilities.desktop import ActionResult


class HostToolGrantTests(unittest.TestCase):
    def test_camera_allow_still_requires_share_grant(self):
        camera = Mock()
        camera.capture_frame.return_value = '/photo.jpg'
        policy = GrantPolicy(lambda key: 'allow' if 'camera.capture' in key else 'ask')
        interact = Mock(return_value={'action': 'decline'})
        with patch('askai.core.agents.camera_tool.grants', policy), patch.dict(sys.modules, {
            'askai.core.component.multimedia.camera': Mock(camera=camera),
        }):
            result = capture_camera({'arguments': {}, 'threadId': 's', 'turnId': 't'}, interact, Mock(), Event())
        self.assertEqual(json.loads(result['contentItems'][0]['text'])['status'], 'cancelled')
        interact.assert_called_once()
        camera.capture_frame.assert_not_called()

    def test_camera_all_allowed_uses_no_input(self):
        camera = Mock()
        camera.capture_frame.return_value = '/photo.jpg'
        interact = Mock(side_effect=AssertionError('No question expected'))
        with patch('askai.core.agents.camera_tool.grants', GrantPolicy(lambda key: 'allow')), patch.dict(sys.modules, {
            'askai.core.component.multimedia.camera': Mock(camera=camera),
        }):
            result = capture_camera({'arguments': {}, 'threadId': 's', 'turnId': 't'}, interact, Mock(), Event())
        self.assertEqual(json.loads(result['contentItems'][0]['text'])['status'], 'completed')

    def test_identity_read_deny_prevents_review_initialization(self):
        with patch('askai.core.agents.enrollment_tool.grants', GrantPolicy(lambda key: 'deny')), patch(
            'askai.core.agents.enrollment_tool._services'
        ) as services, self.assertRaises(GrantDenied):
            register_identities({'arguments': {'review': True}}, Mock(), Mock(), Event())
        services.assert_not_called()


class DesktopGrantTests(unittest.IsolatedAsyncioTestCase):
    async def test_allow_deny_and_ask_apply_on_server_even_without_codex(self):
        for policy_value in ('allow', 'ask', 'deny'):
            with self.subTest(policy_value=policy_value):
                caps = Mock()
                caps.control_music.return_value = ActionResult('control_music', 'completed', 'stop')
                ctx = Mock()
                ctx.session.elicit_form = AsyncMock(return_value=SimpleNamespace(action='accept'))
                server = create_server(caps, GrantPolicy(lambda key: policy_value))
                tool = server._tool_manager.get_tool('control_music')
                if policy_value == 'deny':
                    with self.assertRaises(Exception):
                        await tool.run({'action': 'stop'}, context=ctx)
                    caps.control_music.assert_not_called()
                else:
                    await tool.run({'action': 'stop'}, context=ctx)
                    caps.control_music.assert_called_once_with('stop')
                self.assertEqual(ctx.session.elicit_form.await_count, int(policy_value == 'ask'))
