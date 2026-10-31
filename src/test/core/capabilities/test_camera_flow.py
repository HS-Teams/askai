"""Camera consent and countdown are enforced before touching hardware."""
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch
from pathlib import Path
import sys

from askai.mcp_server import create_server
from askai.core.capabilities.desktop import ActionResult
from askai.core.capabilities.camera_worker import capture


class CameraToolTests(unittest.IsolatedAsyncioTestCase):
    async def invoke(self, decision='accept', operation='capture_camera'):
        capabilities = Mock()
        capabilities.capture_camera.return_value = ActionResult('capture_camera', 'completed', '/tmp/photo.jpg')
        capabilities.open_camera.return_value = ActionResult('open_camera', 'dispatched', 'Photo Booth')
        ctx = Mock()
        ctx.elicit = AsyncMock(return_value=SimpleNamespace(action=decision))
        ctx.report_progress = AsyncMock()
        tool = create_server(capabilities)._tool_manager.get_tool(operation)
        with patch('askai.mcp_server.asyncio.sleep', new_callable=AsyncMock) as sleep:
            result = await tool.run({}, context=ctx)
        return capabilities, ctx, result, sleep

    async def test_accept_counts_down_and_returns_actual_photo(self):
        capabilities, ctx, result, sleep = await self.invoke()
        ctx.elicit.assert_awaited_once()
        self.assertEqual([c.args[2] for c in ctx.report_progress.call_args_list],
                         ['Camera: 3', 'Camera: 2', 'Camera: 1', 'Camera: SHOT'])
        self.assertEqual([c.args for c in sleep.call_args_list], [(1,), (1,), (1,)])
        capabilities.capture_camera.assert_called_once_with(0)
        self.assertEqual(result['target'], '/tmp/photo.jpg')

    async def test_decline_and_cancel_never_access_camera(self):
        for decision in ('decline', 'cancel'):
            for operation in ('capture_camera', 'open_camera'):
                with self.subTest(decision=decision, operation=operation):
                    capabilities, ctx, result, sleep = await self.invoke(decision, operation)
                    capabilities.capture_camera.assert_not_called()
                    capabilities.open_camera.assert_not_called()
                    ctx.report_progress.assert_not_called()
                    sleep.assert_not_called()
                    self.assertEqual(result['status'], 'cancelled')

    async def test_missing_confirmation_fails_closed(self):
        capabilities = Mock()
        ctx = Mock(elicit=AsyncMock(side_effect=RuntimeError('Host unavailable')))
        tool = create_server(capabilities)._tool_manager.get_tool('capture_camera')
        with self.assertRaises(Exception):
            await tool.run({}, context=ctx)
        capabilities.capture_camera.assert_not_called()


class CameraWorkerTests(unittest.TestCase):
    def test_shutter_sound_after_saved_frame_and_camera_released(self):
        cv = Mock()
        cv.VideoCapture.return_value.read.return_value = (True, object())
        with patch.dict(sys.modules, {'cv2': cv}), patch('askai.core.capabilities.camera_worker.subprocess.run') as run:
            capture(0, Path('/tmp/photo.jpg'))
        cv.imwrite.assert_called_once()
        cv.VideoCapture.return_value.release.assert_called_once()
        self.assertTrue(run.call_args.args[0][-1].endswith('/resources/sound-fx/camera-shutter.mp3'))

    def test_bad_frame_releases_camera_without_shutter(self):
        cv = Mock()
        cv.VideoCapture.return_value.read.return_value = (False, None)
        with patch.dict(sys.modules, {'cv2': cv}), patch('askai.core.capabilities.camera_worker.subprocess.run') as run:
            with self.assertRaises(RuntimeError):
                capture(0, Path('/tmp/photo.jpg'))
        cv.VideoCapture.return_value.release.assert_called_once()
        run.assert_not_called()
