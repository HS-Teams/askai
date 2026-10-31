"""One-shot camera capture in a bounded subprocess; no UI or model imports."""

import sys
import logging
import subprocess
from pathlib import Path


def capture(device: int, target: Path):
    import cv2

    camera = cv2.VideoCapture(device)
    try:
        if not camera.isOpened():
            raise RuntimeError(
                "Camera unavailable; check macOS camera permission and device index"
            )
        ok, frame = camera.read()
        if not ok or frame is None:
            raise RuntimeError("Camera returned no frame")
        if not cv2.imwrite(str(target), frame):
            raise RuntimeError("Could not save camera image")
        shutter = Path(__file__).resolve().parents[2] / "resources/sound-fx/camera-shutter.mp3"
        try:
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-loglevel", "error", str(shutter)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=5, check=True,
            )
        except (OSError, subprocess.SubprocessError) as error:
            logging.warning("Camera shutter sound failed: %s", error)
    finally:
        camera.release()


if __name__ == "__main__":
    try:
        capture(int(sys.argv[1]), Path(sys.argv[2]))
    except Exception as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
