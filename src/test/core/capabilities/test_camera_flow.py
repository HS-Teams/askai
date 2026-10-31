"""Camera consent and countdown are enforced before touching hardware."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from askai.mcp_server import create_server
from askai.core.capabilities.desktop import ActionResult


class CameraToolTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, decision='accept', operation='open_camera'):
        capabilities = Mock()
        capabilities.open_camera.return_value = ActionResult('open_camera', 'dispatched', 'Photo Booth')
        ctx = Mock()
        ctx.session.elicit_form = AsyncMock(return_value=SimpleNamespace(action=decision))
        ctx.report_progress = AsyncMock()
        tool = create_server(capabilities)._tool_manager.get_tool(operation)
        with patch('askai.mcp_server.asyncio.sleep', new_callable=AsyncMock) as sleep:
            result = await tool.run({}, context=ctx)
        return capabilities, ctx, result, sleep

    async def test_accept_opens_preview(self):
        capabilities, ctx, result, sleep = await self.invoke()
        ctx.session.elicit_form.assert_awaited_once()
        capabilities.open_camera.assert_called_once()
        self.assertEqual(result['target'], 'Photo Booth')

    async def test_decline_and_cancel_never_access_camera(self):
        for decision in ('decline', 'cancel'):
            for operation in ('open_camera',):
                with self.subTest(decision=decision, operation=operation):
                    capabilities, ctx, result, sleep = await self.invoke(decision, operation)
                    capabilities.open_camera.assert_not_called()
                    ctx.report_progress.assert_not_called()
                    sleep.assert_not_called()
                    self.assertEqual(result['status'], 'cancelled')

    async def test_missing_confirmation_fails_closed(self):
        capabilities = Mock()
        ctx = Mock()
        ctx.session.elicit_form = AsyncMock(side_effect=RuntimeError('Host unavailable'))
        tool = create_server(capabilities)._tool_manager.get_tool('open_camera')
        with self.assertRaises(Exception):
            await tool.run({}, context=ctx)
        capabilities.open_camera.assert_not_called()

