"""Ollama/Phonon speech, with the existing voice preferences and audio cache keys."""

import os
from pathlib import Path
import subprocess
from askai.core.speech.audio_tags import strip_audio_tags
from tempfile import NamedTemporaryFile


class LlamaSpeech:
    def __init__(self, client, configs):
        self._client, self._configs = client, configs

    @property
    def model_name(self) -> str:
        return self._configs.tts_model

    @property
    def voice(self) -> str:
        return self._configs.tts_voice

    def usage(self):
        from askai.core.support.usage import Usage

        return [Usage('Ollama', '-')]

    def voices(self) -> list[str]:
        return self._client.show(self.model_name).get("voices", [])

    def select_voice(self, voice: str) -> None:
        if voice not in self.voices():
            raise ValueError(f"Unknown Ollama voice: {voice}")
        self._configs.tts_voice = voice

    def synthesize(
        self,
        text: str,
        prefix: str = "",
        stream: bool = True,
        playback: bool = True,
        voice: str | None = None,
    ) -> Path | None:
        from askai.core.component.cache_service import cache

        text = strip_audio_tags(text)
        if not text.strip():
            return None
        selected = voice or self.voice
        cache_voice = f"ollama:{self._configs.base_url}:{self.model_name}:{selected}"
        filename, exists = cache.audio_file_path(text, cache_voice, "wav")
        path = Path(filename)
        if not exists:
            self._generate(text, selected, path)
        if playback:
            from askai.core.component.multimedia.audio_player import player

            from askai.core.support.cache_policy import release_transient_audio
            try:
                player.play_audio_file(path, self._configs.tempo)
            finally:
                release_transient_audio(path)
        return path

    def _generate(self, text: str, voice: str, path: Path) -> None:
        with NamedTemporaryFile(dir=path.parent, suffix=".wav") as audio:
            try:
                subprocess.run(
                    ["ollama", "run", self.model_name, "--voice", voice],
                    input=text.encode("utf-8"),
                    stdout=audio,
                    stderr=subprocess.PIPE,
                    check=True,
                    timeout=self._configs.timeout,
                    env={**os.environ, "OLLAMA_HOST": self._configs.base_url},
                )
            except subprocess.CalledProcessError as error:
                raise RuntimeError(
                    f"Ollama speech failed: {error.stderr.decode('utf-8', errors='replace')}"
                ) from error
            except (OSError, subprocess.TimeoutExpired) as error:
                raise RuntimeError(f"Ollama speech failed: {error}") from error
            audio.seek(0)
            header = audio.read(12)
            if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                raise RuntimeError("Ollama speech did not produce a WAV file")
            audio.seek(0)
            path.write_bytes(audio.read())
