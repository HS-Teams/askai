"""Adapt recorded audio to the existing Google or local Whisper recognizer."""

from io import BytesIO
import re


WHISPER_LOGPROB_THRESHOLD = -1.0
WHISPER_CONTROL_TOKEN = re.compile(r'<\|[^<>]*\|>')


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
        locale = language.strip().replace("_", "-")
        if self.provider == 'google':
            return recognizer.recognize_google(audio, language=locale)
        return self._transcribe_whisper(recognizer, audio, locale.split('-', 1)[0].lower())

    @staticmethod
    def _transcribe_whisper(recognizer, audio, language):
        from speech_recognition import UnknownValueError

        # Whisper normally retries uncertain speech with progressively random sampling.
        result = recognizer.recognize_whisper(
            audio, language=language, task='transcribe', temperature=0,
            condition_on_previous_text=False, show_dict=True,
            logprob_threshold=WHISPER_LOGPROB_THRESHOLD,
        )
        text = result['text'].strip()
        segments = result['segments']
        if (not text or not segments
                or all(segment['avg_logprob'] < WHISPER_LOGPROB_THRESHOLD for segment in segments)
                or WHISPER_CONTROL_TOKEN.search(text) or '\ufffd' in text):
            raise UnknownValueError('Whisper could not confidently transcribe the audio')
        return text
