"""OpenAI implementation of the engine speech contract."""

from pathlib import Path
from threading import Event
from typing import Optional
import logging as log

from askai.core.askai_settings import settings
from askai.core.component.cache_service import cache
from askai.core.component.multimedia.audio_player import player


class OpenAISpeech:
    def __init__(self, client, configs):
        self._client = client
        self._configs = configs

    @property
    def model_name(self) -> str:
        return self._configs.tts_model

    @property
    def voice(self) -> str:
        return self._configs.tts_voice

    def voices(self) -> list[str]:
        return [
            "alloy",
            "echo",
            "fable",
            "onyx",
            "nova",
            "shimmer",
            "coral",
            "verse",
            "ballad",
            "ash",
            "sage",
            "marin",
            "cedar",
        ]

    def select_voice(self, voice: str) -> None:
        if voice not in self.voices():
            raise ValueError(f"Unknown OpenAI voice: {voice}")
        settings.put("askai.openai.text.to.speech.voice", voice)
        self._configs.tts_voice = voice

    def synthesize(
        self,
        text: str,
        prefix: str = "",
        stream: bool = True,
        playback: bool = True,
        voice: str | None = None,
    ) -> Optional[Path]:
        """Convert the provided text to speech.
        :param text: The text to convert to speech.
        :param prefix: The prefix of the streamed text.
        :param stream: Whether to stream the text into stdout.
        :param playback: Whether to play back the generated audio file.
        :return: The path to the generated audio file; or None if no file was generated.
        """
        if text:
            speech_file_path, file_exists = cache.audio_file_path(
                text, f"openai:{self.model_name}:{voice or self.voice}", self._configs.tts_format
            )
            if not file_exists:
                log.debug('Audio file "%s" not found in cache. Generating from OpenAI.', speech_file_path)
                with self._client.audio.speech.with_streaming_response.create(
                    input=text,
                    model=self._configs.tts_model,
                    voice=voice or self.voice,
                    response_format=self._configs.tts_format,
                ) as response:
                    response.stream_to_file(speech_file_path)
                    log.debug(f"Audio file created: '%s' at %s", text, speech_file_path)
            else:
                log.debug(f"Audio file found in cache: '%s' at %s", text, speech_file_path)
            if playback:
                from askai.core.speech.playback import synchronized_speech
                from askai.core.support.cache_policy import release_transient_audio
                try:
                    if stream:
                        from askai.cli.speech_renderer import stream_answer
                        from askai.core.support.text_formatter import text_formatter
                        synchronized_speech(
                            speech_file_path, self._configs.tempo, Event(),
                            lambda timing, cancelled: stream_answer(
                                text_formatter.console, text, prefix, timing, cancelled),
                        )
                    else:
                        player.play_audio_file(speech_file_path, self._configs.tempo)
                finally:
                    release_transient_audio(speech_file_path)
            return Path(speech_file_path)
        return None
