"""Sound-effect playback and muting, independent of the speech queue."""
import subprocess
from threading import RLock

_lock = RLock()
_muted = None
_players = set()


def is_muted():
    if _muted is not None:
        return _muted
    from askai.core.askai_settings import settings
    return settings.get_bool('askai.sfx.muted')


def set_muted(muted):
    global _muted
    with _lock:
        _muted = bool(muted)
        if _muted:
            for process in tuple(_players):
                if process.poll() is None:
                    process.terminate()


def play(path, *, tempo=1, loop=None, timeout=None):
    with _lock:
        if is_muted():
            return True
        arguments = ['ffplay', '-af', f'atempo={tempo}', '-v', 'error', '-nodisp', '-autoexit']
        if loop:
            arguments.extend(['-loop', str(loop)])
        process = subprocess.Popen(arguments + [str(path)], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _players.add(process)
    try:
        code = process.wait(timeout=timeout)
        return code == 0 or is_muted()
    finally:
        with _lock:
            _players.discard(process)
        if process.poll() is None:
            process.kill()
            process.wait()
