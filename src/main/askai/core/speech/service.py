"""Lazy speech capabilities that remain stable when the conversation agent changes."""

from threading import RLock
from askai.core.speech.contracts import STTEngine, TTSEngine
from askai.core.speech.factory import create_stt, create_tts


class SpeechService:
    def __init__(self, stt_name: str, tts_name: str):
        self._stt_name, self._tts_name = stt_name, tts_name
        self._lock = RLock()
        self._output = None
        self._stt: STTEngine | None = None
        self._tts: TTSEngine | None = None

    @property
    def stt(self) -> STTEngine:
        if self._stt is None:
            self._stt = create_stt(self._stt_name)
        return self._stt

    @property
    def tts(self) -> TTSEngine:
        if self._tts is None:
            self._tts = create_tts(self._tts_name)
        return self._tts

    def initialize_tts(self) -> str:
        """Probe the selected speech strategy without playback."""
        initialize = getattr(self.tts, "initialize", None)
        return initialize() if initialize else "Ollama voice selected."

    def speak(self, text, on_error, *, present=None, wait=False, immediate=False):
        from askai.core.speech.output_queue import SpeechOutputQueue
        from askai.core.speech.playback import play_speech, synchronized_speech
        from askai.core.askai_configs import configs

        with self._lock:
            if self._output is None:
                self._output = SpeechOutputQueue(
                    lambda text: self.tts.synthesize(text, stream=False, playback=False),
                    lambda path, cancelled: play_speech(path, configs.tempo, cancelled),
                    on_error,
                )
            presentation = (
                (lambda path, cancelled: synchronized_speech(path, configs.tempo, cancelled, present))
                if present is not None else None
            )
            live = getattr(self.tts, 'speak_live', None) if immediate else None
            perform = (lambda text, cancelled: live(text, cancelled, configs.tempo)) if callable(live) else None
            self._output.submit(text, presentation, on_error, perform=perform)
        if wait:
            self._output.wait()

    def cancel_output(self):
        if self._output is not None:
            self._output.cancel()

    def wait_output(self):
        if self._output is not None:
            self._output.wait()

    def close(self):
        if self._output is not None:
            self._output.close()
