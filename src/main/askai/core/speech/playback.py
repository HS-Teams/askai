"""Cancellable ffplay playback owned only by the speech queue."""
import subprocess


def play_speech(path, tempo, cancelled, started=None, timing=None):
    if cancelled.is_set():
        return
    with subprocess.Popen(
        ['ffplay', '-af', f'atempo={tempo}', '-v', 'error',
         *(['-stats'] if timing is not None else []), '-nodisp', '-autoexit', str(path)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE if timing is not None else subprocess.DEVNULL,
    ) as process:
        if started is not None:
            started.set()
        reader = None
        if timing is not None:
            from threading import Thread
            reader = Thread(target=_read_position, args=(process.stderr, timing), daemon=True)
            reader.start()
        try:
            while process.poll() is None:
                if cancelled.wait(.05):
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    return
            if process.returncode:
                raise RuntimeError(f'Speech playback failed (exit {process.returncode})')
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            if reader is not None:
                reader.join()
                timing.finished.set()


def _read_position(stream, timing):
    import re
    line = bytearray()
    while chunk := stream.read(1):
        if chunk in (b'\r', b'\n'):
            match = re.match(rb'\s*(\d+(?:\.\d+)?)\s+(?:M-A|A-V|M-V):', line)
            if match:
                timing.position = float(match[1])
            line.clear()
        elif len(line) < 4096:
            line.extend(chunk)


def synchronized_speech(path, tempo, cancelled, present):
    """Start presentation with playback; keep view rendering in the callback."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import wave
    from askai.core.speech.timing import PlaybackTiming, read_alignment

    try:
        with wave.open(str(path)) as audio:
            duration = audio.getnframes() / audio.getframerate() / tempo
    except (wave.Error, EOFError):
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
            capture_output=True, text=True, check=True, timeout=10,
        )
        duration = float(result.stdout.strip()) / tempo
    started = Event()
    timing = PlaybackTiming(duration, tempo, alignment=read_alignment(path))

    def play():
        try:
            play_speech(path, tempo, cancelled, started, timing)
        finally:
            started.set()
            timing.finished.set()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='askai-playback') as pool:
        playing = pool.submit(play)
        started.wait()
        if playing.done():
            playing.result()
        if not cancelled.is_set():
            try:
                present(timing, cancelled)
            except BaseException:
                cancelled.set()
                raise
        playing.result()
