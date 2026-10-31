"""Delivery cues shared by speech, translation and visual presentation."""
import re


AUDIO_TAG = re.compile(
    r'\[(?:happy|sad|angry|curious|excited|crying|mischievously|'
    r'whispers|shouts|laughs|clears throat|sighs)\]'
)


def strip_audio_tags(text):
    return AUDIO_TAG.sub('', text)


def translate_spoken_text(text, translate):
    if not AUDIO_TAG.search(text):
        return translate(text) if text.strip() else text
    parts, offset = [], 0
    for tag in AUDIO_TAG.finditer(text):
        parts.append(_translate_part(text[offset:tag.start()], translate))
        parts.append(tag.group())
        offset = tag.end()
    parts.append(_translate_part(text[offset:], translate))
    return ''.join(parts)


def _translate_part(text, translate):
    if not text.strip():
        return text
    start = len(text) - len(text.lstrip())
    end = len(text.rstrip())
    return text[:start] + translate(text[start:end]) + text[end:]
