"""Adapt recorded audio to the existing Google or local Whisper recognizer."""

from io import BytesIO


class RecognizerSTT:
    def __init__(self, provider: str):
        if provider not in {"google", "whisper"}:
            raise ValueError(f"Unsupported recognizer: {provider}")
        self.provider = provider

    def transcribe(self, wav_audio: bytes, language: str) -> str:
        from speech_recognition import AudioFile, Recognizer

        recognizer = Recognizer()
        with AudioFile(BytesIO(wav_audio)) as source:
            audio = recognizer.record(source)
        method = (
            recognizer.recognize_google
            if self.provider == "google"
            else recognizer.recognize_whisper
        )
        locale = language.strip().replace("_", "-")
        provider_language = locale if self.provider == "google" else locale.split("-", 1)[0].lower()
        return method(audio, language=provider_language)
