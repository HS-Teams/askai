"""Human choices for grouping face samples into local identities."""
from dataclasses import dataclass
from enum import Enum
import unicodedata
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from askai.core.component.identity_enrollment import EnrollmentFace

MAX_IDENTITY_NAME = 120


class FaceAction(str, Enum):
    NEW = 'new'
    MERGE = 'merge'
    REPLACE = 'replace'
    SKIP = 'skip'


def identity_name(value: str) -> str:
    if not isinstance(value, str) or len(value) > MAX_IDENTITY_NAME or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Identity name must be plain text, up to 120 characters')
    return ' '.join(unicodedata.normalize('NFC', value).split())


def identity_key(value: str) -> str:
    return identity_name(value).casefold()


@dataclass(frozen=True)
class FaceSelection:
    face: "EnrollmentFace"
    action: FaceAction
    name: str = ''
