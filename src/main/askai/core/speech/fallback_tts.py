"""Prefer verified primary speech, retaining the existing Ollama implementation."""
import logging
from pathlib import Path
from threading import RLock
from askai.core.agents.contracts import AgentError


class FallbackTTS:
    def __init__(self, primary, fallback, play, notify=None):
        self._primary, self._fallback_factory, self._play = primary, fallback, play
        self._notify = notify or (lambda provider, reason: None)
        self._lock = RLock()
        self._active = None
        self.status = ''
        self.failure_reason = None

    def initialize(self):
        with self._lock:
            if self._active is None:
                try:
                    self._primary.probe()
                    self._active = self._primary
                    self.status = 'Primary voice ready.'
                    logging.info('TTS: %s', self.status)
                except (AgentError, OSError, ValueError, KeyError) as error:
                    self._use_fallback(error)
            return self.status

    def _use_fallback(self, error):
        self.failure_reason = str(error)
        logging.warning('Primary TTS unavailable: %s', error)
        self._active = self._fallback_factory()
        self.status = 'Primary voice unavailable; using Ollama.'
        logging.info('TTS: %s', self.status)
        self._notify(getattr(self._primary, 'provider_name', 'Primary'), self.failure_reason)

    @property
    def provider_name(self):
        self.initialize()
        return (getattr(self._primary, 'provider_name', 'Primary')
                if self._active is self._primary else 'Ollama (fallback)')

    @property
    def model_name(self):
        self.initialize()
        return self._active.model_name

    @property
    def voice(self):
        self.initialize()
        return self._active.voice

    @property
    def voice_engine(self):
        """Voice management always targets the configured provider."""
        return self._primary

    def voices(self):
        return self._primary.voices()

    def select_voice(self, voice):
        with self._lock:
            previous_voice = self._primary.voice
            self._primary.select_voice(voice)
            try:
                self._primary.probe()
            except (AgentError, OSError, ValueError, KeyError) as error:
                self._primary.select_voice(previous_voice)
                self._use_fallback(error)
                raise
            self._active = self._primary
            self.failure_reason = None
            self.status = 'Primary voice ready.'
            logging.info('TTS: %s', self.status)

    def speak_live(self, text, cancelled, tempo):
        from askai.core.speech.playback import play_speech

        self.initialize()
        if cancelled.is_set():
            return None
        if self._active is self._primary:
            try:
                return self._primary.speak_live(text, cancelled, tempo)
            except (AgentError, OSError, ValueError, KeyError) as error:
                self._use_fallback(error)
        path = self.synthesize(text, playback=False)
        if path and not cancelled.is_set():
            play_speech(path, tempo, cancelled)
        return path

    def synthesize(self, text, prefix='', stream=True, playback=True, voice=None):
        if not text.strip():
            return None
        self.initialize()
        try:
            cached = getattr(self._primary, 'cached_audio', None)
            path = cached(text, voice) if callable(cached) and self._active is not self._primary else None
            if not isinstance(path, Path):
                path = self._active.synthesize(text, prefix, stream, False,
                                               voice if self._active is self._primary else None)
        except (AgentError, OSError, ValueError, KeyError) as error:
            if self._active is not self._primary:
                raise
            self._use_fallback(error)
            # Provider-specific voice names must not overwrite the Phonon preference.
            path = self._active.synthesize(text, prefix, stream, False, None)
        if playback and path:
            from askai.core.support.cache_policy import release_transient_audio
            try:
                self._play(path)
            finally:
                release_transient_audio(path)
        return path
