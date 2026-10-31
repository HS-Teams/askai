"""Cached local language identification; no translator or network requests."""
from functools import lru_cache
from askai.core.support.cache_policy import optional_cache
import re
from lingua import LanguageDetectorBuilder
from askai.language.language import Language

# Syntax carries no natural-language evidence and must not bias detection.
NON_PROSE = re.compile(r'```[\s\S]*?```|`[^`]*`|https?://\S+|%/?\w+%|\[/?\w+\]')
MINIMUM_LANGUAGE_DISTANCE = 0.2


@lru_cache(maxsize=1)
def _detector():
    return LanguageDetectorBuilder.from_all_languages().with_minimum_relative_distance(
        MINIMUM_LANGUAGE_DISTANCE
    ).build()


def prose(text: str) -> str:
    return NON_PROSE.sub(' ', text)


@optional_cache(maxsize=512)
def detect_language(text: str) -> str | None:
    content = prose(text)
    if not any(character.isalpha() for character in content):
        return None
    detected = _detector().detect_language_of(content)
    return detected.iso_code_639_1.name.lower() if detected else None


def language_for(code: str, preferred: Language | None = None) -> Language | None:
    if preferred and preferred.language == code:
        return preferred
    return next((language for language in Language if language.language == code), None)
