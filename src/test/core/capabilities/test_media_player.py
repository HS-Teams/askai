import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
from askai.core.capabilities.media_player import MediaPlayer


class MediaPlayerTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.storage = Path(directory.name)
        self.player = MediaPlayer(self.storage)

    def test_launch_is_literal_and_can_be_controlled_by_next_instance(self):
        process = Mock()
        process.create_time.return_value = 123.0
        child = Mock(pid=42)
        child.wait.side_effect = subprocess.TimeoutExpired("ffplay", 0.2)
        target = self.storage / "song $(test).mp3"
        with patch("shutil.which", return_value="/usr/bin/ffplay"), patch(
            "subprocess.Popen", return_value=child
        ) as popen, patch("psutil.Process", return_value=process):
            result = self.player.play(target, video=False)
            self.assertEqual(result["state"], "started")
            self.assertEqual(
                popen.call_args.args[0],
                [
                    "/usr/bin/ffplay",
                    "-autoexit",
                    "-loglevel",
                    "error",
                    "-nodisp",
                    str(target),
                ],
            )
            self.assertNotIn("shell", popen.call_args.kwargs)
            other = MediaPlayer(self.storage)
            other.control("pause")
            process.suspend.assert_called_once()
            other.control("play")
            process.resume.assert_called_once()
            other.control("stop")
            process.terminate.assert_called_once()
            self.assertFalse(self.player.state_file.exists())

    def test_pid_reuse_never_controls_an_unrelated_process(self):
        self.player.storage.mkdir()
        self.player.state_file.write_text(json.dumps({"pid": 42, "created": 1.0}))
        process = Mock()
        process.create_time.return_value = 2.0
        with patch("psutil.Process", return_value=process), self.assertRaises(
            RuntimeError
        ):
            self.player.control("stop")
        process.terminate.assert_not_called()
        process.resume.assert_not_called()

    def test_video_keeps_window_and_reports_early_decoder_error(self):
        child = Mock()
        child.wait.return_value = 1
        with patch("shutil.which", return_value="ffplay"), patch(
            "subprocess.Popen", return_value=child
        ) as popen, self.assertRaises(RuntimeError):
            self.player.play(self.storage / "movie.mp4", video=True)
        self.assertNotIn("-nodisp", popen.call_args.args[0])
        self.assertFalse(self.player.state_file.exists())

    def test_missing_ffplay_does_not_fall_back_to_music(self):
        with patch("shutil.which", return_value=None), self.assertRaisesRegex(
            RuntimeError, "ffplay"
        ):
            self.player.play(self.storage / "song.mp3", video=False)

    def test_unsupported_control_does_not_signal_processes(self):
        with patch("psutil.Process") as process, self.assertRaises(ValueError):
            self.player.control("next")
        process.assert_not_called()

    def test_status_discards_reused_pid(self):
        self.player.storage.mkdir()
        self.player.state_file.write_text(json.dumps({'pid': 42, 'created': 1.0}))
        with patch('psutil.Process') as process:
            process.return_value.create_time.return_value = 2.0
            self.assertIsNone(self.player.status())

    def test_volume_clamps_to_system_limits(self):
        for current, delta, expected in ((98, 5, 100), (2, -5, 0)):
            with patch('subprocess.run', return_value=Mock(stdout=str(current))) as run:
                self.assertEqual(self.player.volume(delta), expected)
                self.assertEqual(run.call_args.args[0][-1], f'set volume output volume {expected}')
