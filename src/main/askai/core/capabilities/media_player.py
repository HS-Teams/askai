"""Persistent ownership of ffplay playback across short-lived MCP sessions."""

from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import psutil


class PlaybackEnded(RuntimeError):
    """The owned media process ended before a control could be applied."""


class MediaPlayer:
    def __init__(self, storage: Path):
        self.storage = storage / "playback"
        self.state_file = self.storage / "active.json"

    @contextmanager
    def _locked(self):
        self.storage.mkdir(parents=True, exist_ok=True)
        with (self.storage / "lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _active(self):
        if not self.state_file.exists():
            return None
        state = json.loads(self.state_file.read_text())
        try:
            process = psutil.Process(state["pid"])
            if (
                process.create_time() == state["created"]
                and process.status() != psutil.STATUS_ZOMBIE
            ):
                return process
        except psutil.NoSuchProcess:
            pass
        self.state_file.unlink(missing_ok=True)
        return None

    @staticmethod
    def _stop(process):
        try:
            process.resume()  # A suspended player must run to handle termination.
            process.terminate()
            try:
                process.wait(timeout=3)
            except psutil.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        except psutil.NoSuchProcess:
            pass

    def play(self, path: Path, video: bool) -> dict:
        executable = shutil.which("ffplay")
        if not executable:
            raise RuntimeError(
                "ffplay is required; install FFmpeg before playing media"
            )
        command = [executable, "-autoexit", "-loglevel", "error"]
        if not video:
            command.append("-nodisp")
        command.append(str(path))
        with self._locked():
            if active := self._active():
                self._stop(active)
            self.state_file.unlink(missing_ok=True)
            log_path = self.storage / "ffplay.log"
            with log_path.open("w") as errors:
                child = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=errors,
                    start_new_session=True,
                )
                try:
                    code = child.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    process = psutil.Process(child.pid)
                    state = {
                        "pid": child.pid,
                        "created": process.create_time(),
                        "path": str(path),
                    }
                    temp = self.state_file.with_suffix(".tmp")
                    temp.write_text(json.dumps(state))
                    temp.replace(self.state_file)
                    return {"player": "ffplay", "state": "started", "pid": child.pid}
            if code != 0:
                raise RuntimeError(f"ffplay failed: {log_path.read_text()[-2000:]}")
            return {"player": "ffplay", "state": "completed"}

    def control(self, action: str) -> dict:
        if action not in {"play", "pause", "stop"}:
            raise ValueError(
                "Choose play (resume), pause or stop; playlists are not supported"
            )
        with self._locked():
            process = self._active()
            if process is None:
                raise PlaybackEnded("No active AskAI media playback")
            try:
                if action == "stop":
                    self._stop(process)
                    self.state_file.unlink(missing_ok=True)
                elif action == "pause":
                    process.suspend()
                else:
                    process.resume()
            except psutil.NoSuchProcess as error:
                self.state_file.unlink(missing_ok=True)
                raise PlaybackEnded("Playback has already ended") from error
            return {
                "player": "ffplay",
                "state": {"play": "playing", "pause": "paused", "stop": "stopped"}[
                    action
                ],
            }

    def status(self) -> dict | None:
        with self._locked():
            process = self._active()
            if process is None:
                return None
            state = json.loads(self.state_file.read_text())
            try:
                status = process.status()
            except psutil.NoSuchProcess:
                self.state_file.unlink(missing_ok=True)
                return None
            if status == psutil.STATUS_ZOMBIE:
                self.state_file.unlink(missing_ok=True)
                return None
            return {**state, "state": "paused" if status == psutil.STATUS_STOPPED else "playing"}

    @staticmethod
    def volume(change: int = 0) -> int:
        """Read or adjust macOS output volume, independently of media ownership."""
        current = int(subprocess.run(
            ["osascript", "-e", "output volume of (get volume settings)"],
            capture_output=True, text=True, check=True,
        ).stdout.strip())
        value = max(0, min(100, current + change))
        if change:
            subprocess.run(["osascript", "-e", f"set volume output volume {value}"],
                           capture_output=True, text=True, check=True)
        return value
