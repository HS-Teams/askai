import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from askai.core.capabilities.desktop import DesktopCapabilities
from askai.core.capabilities.camera_worker import capture


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.desktop = DesktopCapabilities(self.base)
        patcher = patch("askai.core.capabilities.desktop.sys.platform", "darwin")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_open_path_keeps_shell_characters_literal(self):
        target = self.base / "document $(touch stolen).txt"
        target.touch()
        with patch("subprocess.run", return_value=Mock(stdout="")) as run:
            result = self.desktop.open_path(str(target))
        self.assertEqual(result.status, "dispatched")
        self.assertEqual(run.call_args.args[0], ["open", str(target.resolve())])
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_missing_and_relative_paths_never_launch(self):
        with patch("subprocess.run") as run:
            for path in ("relative.txt", str(self.base / "missing")):
                with self.subTest(path=path), self.assertRaises(
                    (ValueError, FileNotFoundError)
                ):
                    self.desktop.open_path(path)
            run.assert_not_called()

    def test_music_controls_delegate_to_owned_player(self):
        with patch.object(
            self.desktop._player, "control", return_value={"state": "paused"}
        ) as control:
            result = self.desktop.control_music("pause")
            self.assertEqual(result.details["state"], "paused")
            control.assert_called_once_with("pause")

    def test_media_routes_audio_and_video_to_ffplay(self):
        with patch.object(
            self.desktop._player, "play", return_value={"state": "started"}
        ) as play:
            for name, video in [
                ("song.mp3", False),
                ("movie.mp4", True),
                ("lossless.flac", False),
            ]:
                target = self.base / name
                target.touch()
                result = self.desktop.open_path(str(target))
                self.assertEqual(result.status, "started")
                play.assert_called_with(target.resolve(), video=video)
            other = self.base / "script.sh"
            other.touch()
            with self.assertRaises(ValueError):
                self.desktop.play_music(str(other))

    def test_camera_is_released_on_read_failure(self):
        cv2 = Mock()
        cv2.VideoCapture.return_value.read.return_value = (False, None)
        with patch.dict(sys.modules, {"cv2": cv2}), self.assertRaises(RuntimeError):
            capture(0, self.base / "photo.jpg")
        cv2.VideoCapture.return_value.release.assert_called_once()

    def test_camera_timeout_cleans_partial_file(self):
        def fail(arguments, timeout):
            Path(arguments[-1]).write_bytes(b"partial")
            raise RuntimeError("timeout")

        with patch.object(self.desktop, "_run", side_effect=fail), self.assertRaises(
            RuntimeError
        ):
            self.desktop.capture_camera()
        self.assertEqual(list((self.base / "photos").iterdir()), [])

    def test_camera_preview_does_not_capture(self):
        with patch.object(self.desktop, "open_application") as open_app:
            open_app.return_value = Mock(status="dispatched", target="Photo Booth")
            self.desktop.open_camera()
            open_app.assert_called_once_with("Photo Booth")
