"""Exercise the original Camera methods without initializing devices or app storage."""
import ast
from pathlib import Path
import unittest
from unittest.mock import Mock


def camera_methods():
    source = Path(__file__).parents[3] / 'main/askai/core/component/multimedia/camera.py'
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Camera')
    cls.bases = []
    cls.keywords = []
    cls.body = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in ('countdown', 'capture_frame')]
    tree.body = [cls]
    scope = dict(monotonic=Mock(side_effect=[0, 0.1, 1, 1, 1.1, 2, 2, 2.1, 3]),
                 events=Mock(), AIReply=Mock(), msg=Mock(), player=Mock(), pause=Mock(),
                 CameraAccessFailure=RuntimeError, cv2=Mock(), PHOTO_DIR='/photos',
                 build_img_path=Mock(return_value='/photos/test-PHOTO.jpg'), now_ms=Mock(return_value=123))
    exec(compile(ast.fix_missing_locations(tree), str(source), 'exec'), scope)
    camera = scope['Camera']()
    camera.initialize = Mock()
    camera.shutdown = Mock()
    camera._cam = Mock()
    return camera, scope


class CameraCountdownTests(unittest.TestCase):
    def test_three_clicks_fresh_frames_then_shutter(self):
        camera, scope = camera_methods()
        frames = [object() for _ in range(4)]
        camera._cam.read.side_effect = [(True, frame) for frame in frames]
        timeline = Mock()
        timeline.attach_mock(camera.initialize, 'initialize')
        timeline.attach_mock(scope['player'].play_sfx, 'sound')
        timeline.attach_mock(scope['cv2'].imwrite, 'save')
        timeline.attach_mock(camera.shutdown, 'shutdown')
        self.assertEqual(camera.capture_frame(), '/photos/test-PHOTO.jpg')
        self.assertEqual([c.args[0] for c in scope['msg'].smile.call_args_list], [3, 2, 1])
        self.assertEqual([c.args[0] for c in scope['player'].play_sfx.call_args_list],
                         ['ui/click', 'ui/click', 'ui/click', 'ui/camera-shutter'])
        scope['cv2'].imwrite.assert_called_once_with('/photos/test-PHOTO.jpg', frames[-1])
        self.assertEqual([c[0] for c in timeline.mock_calls],
                         ['initialize', 'sound', 'sound', 'sound', 'save', 'sound', 'shutdown'])

    def test_bad_warmup_frame_releases_camera_without_shutter_or_photo(self):
        camera, scope = camera_methods()
        camera._cam.read.return_value = (False, None)
        with self.assertRaises(RuntimeError):
            camera.capture_frame()
        camera.shutdown.assert_called_once()
        scope['cv2'].imwrite.assert_not_called()
        self.assertNotIn('ui/camera-shutter', [c.args[0] for c in scope['player'].play_sfx.call_args_list])
