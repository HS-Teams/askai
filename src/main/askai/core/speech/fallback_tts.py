"""Prefer verified Codex speech, retaining the existing Ollama implementation."""
import logging
from askai.core.agents.contracts import AgentError


class FallbackTTS:
    def __init__(self, primary, fallback, play):
        self._primary, self._fallback_factory, self._play = primary, fallback, play
        self._active = None
        self.status = ''
        self.failure_reason = None

    def initialize(self):
        if self._active is None:
            try:
                self._primary.probe()
                self._active = self._primary
                self.status = 'Codex voice ready.'
                logging.info('TTS: %s', self.status)
            except (AgentError, OSError, ValueError, KeyError) as error:
                self._use_fallback(error)
        return self.status

    def _use_fallback(self, error):
        self.failure_reason = str(error)
        logging.debug('Codex TTS unavailable: %s', error)
        self._active = self._fallback_factory()
        self.status = 'Codex voice unavailable; using Ollama.'
        logging.info('TTS: %s', self.status)

    @property
    def model_name(self):
        self.initialize()
        return self._active.model_name

    @property
    def voice(self):
        self.initialize()
        return self._active.voice

    def voices(self):
        self.initialize()
        return self._active.voices()

    def select_voice(self, voice):
        self.initialize()
        self._active.select_voice(voice)

    def synthesize(self, text, prefix='', stream=True, playback=True, voice=None):
        if not text.strip():
            return None
        self.initialize()
        try:
            path = self._active.synthesize(text, prefix, stream, False, voice)
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
