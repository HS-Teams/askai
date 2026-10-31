"""Independent speech engine contracts."""

from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class TTSEngine(Protocol):
    """Speech synthesis and voice selection, independent of conversation agents."""

    @property
    def model_name(self) -> str: ...

    @property
    def voice(self) -> str: ...

    def voices(self) -> list[str]: ...

    def select_voice(self, voice: str) -> None:
        """Validate and persist the selection for this provider."""
        ...

    def synthesize(
        self,
        text: str,
        prefix: str = "",
        stream: bool = True,
        playback: bool = True,
        voice: str | None = None,
    ) -> Path | None:
        """Return a cached/generated audio path, or None for empty text.

        A voice override must not change the saved selection. Cache identity
        must include provider, model, voice and text. Failed synthesis must
        raise an exception and must not publish a cache entry.
        """
        ...


@runtime_checkable
class STTEngine(Protocol):
    """Transcription only: audio capture belongs to the caller."""

    def transcribe(self, wav_audio: bytes, language: str) -> str:
        """Transcribe recorded WAV bytes without capturing input or rendering UI."""
        ...
