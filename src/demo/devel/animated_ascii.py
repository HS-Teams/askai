"""Stream local video as terminal ASCII, paced to its audio when present."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from threading import Event
from time import monotonic

import cv2
from PIL import Image
from PIL.Image import Resampling

from askai.core.speech.playback import play_speech
from askai.core.speech.timing import PlaybackTiming

PALETTES = {1: " .:-=+*#%@", 2: " ▁▂▃▄▅▆▇█▊", 3: " ░▒▓█▓▒░▒▓"}
DEFAULT_PALETTE = PALETTES[1]
FPS = 10
CELL_ASPECT = 0.4
VIDEO_DIR = Path.home() / 'Movies'


def frame_to_ascii(image, width, palette=DEFAULT_PALETTE, reverse=True, *, height=None, cell_aspect=CELL_ASPECT):
    if width < 1 or (height is not None and height < 1) or not palette or not math.isfinite(cell_aspect) or cell_aspect <= 0:
        raise ValueError('Positive dimensions, cell aspect and a nonempty palette are required')
    palette = palette[::-1] if reverse else palette
    ratio = image.height / image.width * cell_aspect
    if height is not None:
        width = min(width, max(1, int(height / ratio)))
    rows = max(1, int(width * ratio))
    if height is not None:
        rows = min(rows, height)
    scaled = image.convert('L').resize((width, rows), Resampling.LANCZOS)
    pixels = ''.join(palette[min(value * len(palette) // 256, len(palette) - 1)] for value in scaled.tobytes())
    return '\n'.join(pixels[start:start + width] for start in range(0, len(pixels), width))


def image_to_ascii(frame_path, width, palette, reverse):
    with Image.open(frame_path) as image:
        return frame_to_ascii(image, width, palette, reverse)


def print_ascii_image(image, output=None, size=None):
    output = output or sys.stdout
    cols, rows = size or shutil.get_terminal_size()
    lines = image.splitlines()[:max(0, rows - 1)]
    # One frame write; avoid the last column/row to prevent terminal scrolling.
    body = '\n'.join(line[:max(0, cols - 1)].center(max(0, cols - 1)) + '\x1b[K' for line in lines)
    output.write('\x1b[H' + body + '\x1b[J')
    output.flush()


@contextmanager
def terminal_screen(output, cancelled):
    previous = {}
    def stop(signum, frame):
        cancelled.set()
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, stop)
        output.write('\x1b[?1049h\x1b[2J\x1b[?25l')
        output.flush()
        yield
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)
        output.write('\x1b[?25h\x1b[?1049l')
        output.flush()


def video_info(path):
    result = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type:format=duration', '-of', 'json', str(path)],
        capture_output=True, text=True, check=True, timeout=10,
    )
    info = json.loads(result.stdout)
    return float(info['format']['duration']), any(s['codec_type'] == 'audio' for s in info['streams'])


def render_video(capture, width, fps, cancelled, clock, *, finished=lambda: False, output=None, cell_aspect=CELL_ASPECT):
    source_fps = capture.get(cv2.CAP_PROP_FPS)
    if not math.isfinite(source_fps) or source_fps <= 0:
        raise ValueError('Video does not report a valid frame rate')
    fps = min(fps, source_fps)
    next_tick = 0.0
    while not cancelled.is_set() and not finished():
        now = clock()
        if now < next_tick:
            cancelled.wait(min(.02, next_tick - now))
            continue
        wanted = int(now * source_fps)
        # Decode forward without retaining frames; skip rendering stale frames.
        while capture.get(cv2.CAP_PROP_POS_FRAMES) < wanted:
            if not capture.grab():
                return
        ok, frame = capture.read()
        if not ok:
            return
        cols, rows = shutil.get_terminal_size()
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        ascii_frame = frame_to_ascii(image, min(width, max(1, cols - 1)), height=max(1, rows - 1), cell_aspect=cell_aspect)
        print_ascii_image(ascii_frame, output, (cols, rows))
        next_tick = (int(now * fps) + 1) / fps


def play(video_name, width=80, *, fps=FPS, cell_aspect=CELL_ASPECT):
    if width < 1 or not math.isfinite(fps) or fps <= 0:
        raise ValueError('Width and FPS must be positive')
    path = Path(os.path.expandvars(video_name)).expanduser()
    if not path.exists() and not path.is_absolute():
        path = VIDEO_DIR / path
    path = path.resolve(strict=True)
    duration, has_audio = video_info(path)
    capture = cv2.VideoCapture(str(path))
    cancelled = Event()
    try:
        if not capture.isOpened():
            raise ValueError(f'Cannot decode video: {path}')
        with terminal_screen(sys.stdout, cancelled), ThreadPoolExecutor(max_workers=1) as pool:
            audio = None
            try:
                if has_audio:
                    timing = PlaybackTiming(duration)
                    audio = pool.submit(play_speech, path, 1, cancelled, timing=timing)
                    render_video(capture, width, fps, cancelled, lambda: timing.position,
                                 finished=audio.done, cell_aspect=cell_aspect)
                    audio.result()
                else:
                    started = monotonic()
                    render_video(capture, width, fps, cancelled, lambda: monotonic() - started,
                                 cell_aspect=cell_aspect)
            finally:
                cancelled.set()
    finally:
        capture.release()


if __name__ == "__main__":
    play("/Users/hjunior/GIT-Repository/GitHub/rpg-game/src/webapp/src/assets/video/welcome-dragon_4K.webm", 50)
    # asc_img = image_to_ascii(expandvars("${DESKTOP}/robot.png"), 74, DEFAULT_PALETTE, True)
    # print_ascii_image(asc_img)
