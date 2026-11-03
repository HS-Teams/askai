"""Own one gesture worker; native output goes to a log, events use a private pipe."""
import atexit
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from threading import Event, Lock, Thread

_lock = Lock()
_process = None
STARTUP_TIMEOUT_SECONDS = 120


def stop():
    with _lock:
        process = _process
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def launch(camera_index, storage, labels, notify, *, wait_ready=False, on_progress=lambda stage: None):
    global _process
    with _lock:
        if _process is not None and _process.poll() is None:
            raise RuntimeError('Gesture control is already active')
        log_path = Path(storage) / 'logs' / 'gestures.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        read_fd, write_fd = os.pipe()
        try:
            with log_path.open('ab') as output:
                _process = subprocess.Popen(
                    [sys.executable, '-m', 'askai.gestures.worker', str(camera_index), str(write_fd),
                     json.dumps(labels)], stdout=output, stderr=output, stdin=subprocess.DEVNULL,
                    pass_fds=(write_fd,), start_new_session=True)
        except BaseException:
            os.close(read_fd)
            raise
        finally:
            os.close(write_fd)
        process = _process
    ready = Event()
    startup = []

    def deliver(kind):
        if isinstance(kind, dict) and kind.get('type') == 'loading':
            on_progress(kind['stage'])
            return
        if wait_ready and not ready.is_set() and kind in {'started', 'stopped', 'failed'}:
            startup.append(kind)
            ready.set()
        else:
            notify(kind)

    Thread(target=_read_events, args=(read_fd, process, deliver), daemon=True).start()
    if wait_ready:
        if not ready.wait(STARTUP_TIMEOUT_SECONDS):
            stop()
            raise RuntimeError(f'Gesture startup timed out. See {log_path}')
        if startup[0] != 'started':
            raise RuntimeError(f'Gesture control failed to start. See {log_path}')
        return {'status': 'started', 'pid': process.pid, 'log': str(log_path)}
    return {'status': 'starting', 'pid': process.pid, 'log': str(log_path)}


def _read_events(fd, process, notify):
    with os.fdopen(fd) as stream:
        for line in stream:
            try:
                notify(json.loads(line))
            except Exception:
                logging.exception('Cannot deliver gesture event')
    code = process.wait()
    try:
        notify('stopped' if code == 0 else 'failed')
    except Exception:
        logging.exception('Cannot deliver gesture completion')


atexit.register(stop)
