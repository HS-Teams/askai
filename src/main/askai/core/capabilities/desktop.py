"""Typed desktop actions; paths and application names are never shell code."""

from dataclasses import dataclass, field
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from askai.core.capabilities.media_player import MediaPlayer


@dataclass(frozen=True)
class ActionResult:
    operation: str
    status: str
    target: str
    details: dict = field(default_factory=dict)


class DesktopCapabilities:
    AUDIO_SUFFIXES = {
        ".mp3",
        ".m4a",
        ".aac",
        ".wav",
        ".aiff",
        ".aif",
        ".flac",
        ".ogg",
        ".opus",
        ".wma",
    }
    VIDEO_SUFFIXES = {
        ".mp4",
        ".m4v",
        ".mov",
        ".mkv",
        ".avi",
        ".webm",
        ".mpeg",
        ".mpg",
        ".wmv",
    }

    def __init__(self, storage: Path):
        self.storage = storage
        self._player = MediaPlayer(storage)

    @staticmethod
    def _macos():
        if sys.platform != "darwin":
            raise RuntimeError("These desktop capabilities currently require macOS")

    @staticmethod
    def _run(arguments: list[str], timeout: int = 20) -> str:
        try:
            result = subprocess.run(
                arguments, capture_output=True, text=True, check=True, timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as error:
            raise RuntimeError(
                error.stderr.strip() or f"{arguments[0]} failed"
            ) from error
        except (OSError, subprocess.TimeoutExpired) as error:
            raise RuntimeError(f"Desktop action failed: {error}") from error

    @staticmethod
    def _path(path: str) -> Path:
        target = Path(path).expanduser()
        if not target.is_absolute():
            raise ValueError("Use an absolute path or ~/path")
        target = target.resolve(strict=True)
        if not (target.is_file() or target.is_dir()):
            raise ValueError("Target must be a regular file or directory")
        return target

    def open_path(self, path: str) -> ActionResult:
        self._macos()
        target = self._path(path)
        if (
            target.is_file()
            and target.suffix.lower() in self.AUDIO_SUFFIXES | self.VIDEO_SUFFIXES
        ):
            return self._play_media(target)
        self._run(["open", str(target)])
        return ActionResult("open_path", "dispatched", str(target))

    def open_application(self, name: str) -> ActionResult:
        self._macos()
        if not name.strip() or name.startswith("-") or "\x00" in name:
            raise ValueError("An application name is required")
        self._run(["open", "-a", name])
        return ActionResult("open_application", "dispatched", name)

    def _play_media(self, target: Path) -> ActionResult:
        details = self._player.play(
            target, video=target.suffix.lower() in self.VIDEO_SUFFIXES
        )
        return ActionResult("play_media", details["state"], str(target), details)

    def play_music(self, path: str) -> ActionResult:
        self._macos()
        target = self._path(path)
        if (
            not target.is_file()
            or target.suffix.lower() not in self.AUDIO_SUFFIXES | self.VIDEO_SUFFIXES
        ):
            raise ValueError("Select a supported local audio or video file")
        return self._play_media(target)

    def control_music(self, action: str) -> ActionResult:
        self._macos()
        return ActionResult(
            "control_media", "completed", "ffplay", self._player.control(action)
        )

    def open_camera(self) -> ActionResult:
        result = self.open_application("Photo Booth")
        return ActionResult(
            "open_camera",
            result.status,
            result.target,
            {"note": "Preview requested. No image has been captured by AskAI."},
        )

    def capture_camera(self, device: int = 0) -> ActionResult:
        self._macos()
        if device < 0:
            raise ValueError("Camera device must be non-negative")
        folder = self.storage / "photos"
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{uuid4().hex}.jpg"
        try:
            self._run(
                [
                    sys.executable,
                    "-m",
                    "askai.core.capabilities.camera_worker",
                    str(device),
                    str(target),
                ],
                timeout=20,
            )
            if not target.is_file() or target.stat().st_size == 0:
                raise RuntimeError("Camera did not produce an image")
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        return ActionResult(
            "capture_camera", "completed", str(target), {"bytes": target.stat().st_size}
        )
