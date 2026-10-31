"""Ordered speech output, isolated from response generation and UI threads."""
import logging
from queue import Queue, Full, Empty
from threading import Event, Lock, Thread
from askai.core.support.performance import timed


class SpeechOutputQueue:
    MAX_PENDING = 8

    def __init__(self, synthesize, play, on_error):
        self._synthesize, self._play, self._on_error = synthesize, play, on_error
        self._queue = Queue(maxsize=self.MAX_PENDING)
        self._lock = Lock()
        self._generation = Event()
        self._closed = False
        self._worker = Thread(target=self._run, name='askai-speech', daemon=True)
        self._worker.start()

    def submit(self, text, present=None, on_error=None):
        if not text.strip():
            return
        with self._lock:
            if self._closed:
                raise RuntimeError('Speech output is closed')
            try:
                self._queue.put_nowait((text, self._generation, present, on_error))
            except Full as error:
                raise RuntimeError('Speech output queue is full') from error

    def cancel(self):
        with self._lock:
            self._generation.set()
            self._generation = Event()
            while True:
                try:
                    self._queue.get_nowait()
                except Empty:
                    break
                self._queue.task_done()

    def wait(self):
        self._queue.join()

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        self.cancel()
        self._queue.put_nowait(None)
        self._worker.join()

    def _run(self):
        while True:
            job = self._queue.get()
            path = None
            try:
                if job is None:
                    return
                text, cancelled, present, on_error = job
                if cancelled.is_set():
                    continue
                with timed('speech.synthesis'):
                    path = self._synthesize(text)
                if path and not cancelled.is_set():
                    with timed('speech.playback'):
                        (present or self._play)(path, cancelled)
            except Exception as error:
                if not self._closed and not cancelled.is_set():
                    try:
                        (on_error or self._on_error)(error)
                    except Exception:
                        logging.exception("Speech error handler failed")
            finally:
                from askai.core.support.cache_policy import release_transient_audio
                release_transient_audio(path)
                self._queue.task_done()
