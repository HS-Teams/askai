"""Cancellable ffplay playback owned only by the speech queue."""
import subprocess


def play_speech(path, tempo, cancelled, started=None):
    if cancelled.is_set():
        return
    with subprocess.Popen(
        ['ffplay', '-af', f'atempo={tempo}', '-v', 'error', '-nodisp', '-autoexit', str(path)],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    ) as process:
        if started is not None:
            started.set()
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


def synchronized_speech(path, tempo, cancelled, present, start_delay=0):
    """Start presentation with playback; keep view rendering in the callback."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    import wave

    with wave.open(str(path)) as audio:
        duration = audio.getnframes() / audio.getframerate() / tempo
    started = Event()

    def play():
        try:
            play_speech(path, tempo, cancelled, started)
        finally:
            started.set()

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix='askai-playback') as pool:
        playing = pool.submit(play)
        started.wait()
        if playing.done():
            playing.result()
        if not cancelled.wait(start_delay):
            try:
                present(duration, cancelled)
            except BaseException:
                cancelled.set()
                raise
        playing.result()
