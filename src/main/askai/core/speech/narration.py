"""Explicit narration markup shared by validation and presentation."""
from dataclasses import dataclass
import re
from askai.core.speech.audio_tags import strip_audio_tags, translate_spoken_text


@dataclass(frozen=True)
class Narration:
    before: str
    spoken: str
    after: str

    @property
    def visible(self):
        return self.before + strip_audio_tags(self.spoken) + self.after


def parse_narration(text: str, *, required: bool = False) -> Narration:
    tags = re.findall(r'</?tts\b[^>]*>', text, flags=re.IGNORECASE)
    if not tags and not required:
        return Narration(text, '', '')
    if tags != ['<TTS>', '</TTS>']:
        raise ValueError('Final answer requires exactly one <TTS>...</TTS> section')
    before, _, remainder = text.partition('<TTS>')
    spoken, _, after = remainder.partition('</TTS>')
    if required and after.strip():
        raise ValueError("The TTS section must be the final section of the answer")
    if not strip_audio_tags(spoken).strip():
        raise ValueError('The TTS section must contain narration text')
    return Narration(before, spoken, after)


def translate_narration(text, translate):
    narration = parse_narration(text)
    if not narration.spoken:
        return translate(text)
    def part(value):
        return translate(value) if value.strip() else value
    return part(narration.before) + '<TTS>' + translate_spoken_text(narration.spoken, translate) + '</TTS>' + part(narration.after)
