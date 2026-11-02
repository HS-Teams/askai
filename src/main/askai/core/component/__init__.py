# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.component
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .internet_service import ASKAI_INTERNET_DATA_KEY
    from .answer_validator import Assessment
    from .multimedia.audio_player import AudioPlayer
    from .internet_service import CATEGORY_ICONS
    from .search_presentation import CATEGORY_ICONS
    from .cache_service import CacheService
    from .multimedia.camera import Camera
    from .faces.models import DEFAULT_THRESHOLD
    from .faces.models import DetectedFace
    from .retrieval import Document
    from .identity_enrollment import EnrollmentFace
    from .identity_enrollment import EnrollmentPhoto
    from .faces.selections import FaceAction
    from .faces.index import FaceIndex
    from .faces.models import FaceModels
    from .faces.index import FaceRecord
    from .faces.selections import FaceSelection
    from .multimedia.recorder import GOOGLE
    from .geo_location import GeoLocation
    from .identity_enrollment import IdentityEnrollment
    from .internet_service import InternetService
    from .faces.selections import MAX_IDENTITY_NAME
    from .faces.selections import MERGE
    from .faces.migration import MIGRATION_KEY
    from .faces.models import MODEL_FILES
    from .faces.models import MODEL_VERSION
    from .faces.selections import NEW
    from .multimedia.recorder import OPEN_AI
    from .rag_provider import RAGProvider
    from .faces.selections import REPLACE
    from .multimedia.recorder import RecognitionApi
    from .multimedia.recorder import Recorder
    from .multimedia.audio_player import SFX_DIR
    from .internet_service import SITE_ICONS
    from .faces.selections import SKIP
    from .scheduler import Scheduler
    from .summarizer import Summarizer
    from .faces.models import VECTOR_SIZE
    from .retrieval import VectorIndex
    from .cache_service import is


_EXPORTS = {
    'ASKAI_INTERNET_DATA_KEY': ('internet_service', 'ASKAI_INTERNET_DATA_KEY'),
    'Assessment': ('answer_validator', 'Assessment'),
    'AudioPlayer': ('multimedia.audio_player', 'AudioPlayer'),
    'CATEGORY_ICONS': ('internet_service', 'CATEGORY_ICONS'),
    'CATEGORY_ICONS': ('search_presentation', 'CATEGORY_ICONS'),
    'CacheService': ('cache_service', 'CacheService'),
    'Camera': ('multimedia.camera', 'Camera'),
    'DEFAULT_THRESHOLD': ('faces.models', 'DEFAULT_THRESHOLD'),
    'DetectedFace': ('faces.models', 'DetectedFace'),
    'Document': ('retrieval', 'Document'),
    'EnrollmentFace': ('identity_enrollment', 'EnrollmentFace'),
    'EnrollmentPhoto': ('identity_enrollment', 'EnrollmentPhoto'),
    'FaceAction': ('faces.selections', 'FaceAction'),
    'FaceIndex': ('faces.index', 'FaceIndex'),
    'FaceModels': ('faces.models', 'FaceModels'),
    'FaceRecord': ('faces.index', 'FaceRecord'),
    'FaceSelection': ('faces.selections', 'FaceSelection'),
    'GOOGLE': ('multimedia.recorder', 'GOOGLE'),
    'GeoLocation': ('geo_location', 'GeoLocation'),
    'IdentityEnrollment': ('identity_enrollment', 'IdentityEnrollment'),
    'InternetService': ('internet_service', 'InternetService'),
    'MAX_IDENTITY_NAME': ('faces.selections', 'MAX_IDENTITY_NAME'),
    'MERGE': ('faces.selections', 'MERGE'),
    'MIGRATION_KEY': ('faces.migration', 'MIGRATION_KEY'),
    'MODEL_FILES': ('faces.models', 'MODEL_FILES'),
    'MODEL_VERSION': ('faces.models', 'MODEL_VERSION'),
    'NEW': ('faces.selections', 'NEW'),
    'OPEN_AI': ('multimedia.recorder', 'OPEN_AI'),
    'RAGProvider': ('rag_provider', 'RAGProvider'),
    'REPLACE': ('faces.selections', 'REPLACE'),
    'RecognitionApi': ('multimedia.recorder', 'RecognitionApi'),
    'Recorder': ('multimedia.recorder', 'Recorder'),
    'SFX_DIR': ('multimedia.audio_player', 'SFX_DIR'),
    'SITE_ICONS': ('internet_service', 'SITE_ICONS'),
    'SKIP': ('faces.selections', 'SKIP'),
    'Scheduler': ('scheduler', 'Scheduler'),
    'Summarizer': ('summarizer', 'Summarizer'),
    'VECTOR_SIZE': ('faces.models', 'VECTOR_SIZE'),
    'VectorIndex': ('retrieval', 'VectorIndex'),
    'is': ('cache_service', 'is')
}

def __getattr__(name):
    if name in _EXPORTS:
        module, attr = _EXPORTS[name]
        mod = importlib.import_module(f"{__name__}.{module}")
        value = getattr(mod, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    'ASKAI_INTERNET_DATA_KEY',
    'Assessment',
    'AudioPlayer',
    'CATEGORY_ICONS',
    'CATEGORY_ICONS',
    'CacheService',
    'Camera',
    'DEFAULT_THRESHOLD',
    'DetectedFace',
    'Document',
    'EnrollmentFace',
    'EnrollmentPhoto',
    'FaceAction',
    'FaceIndex',
    'FaceModels',
    'FaceRecord',
    'FaceSelection',
    'GOOGLE',
    'GeoLocation',
    'IdentityEnrollment',
    'InternetService',
    'MAX_IDENTITY_NAME',
    'MERGE',
    'MIGRATION_KEY',
    'MODEL_FILES',
    'MODEL_VERSION',
    'NEW',
    'OPEN_AI',
    'RAGProvider',
    'REPLACE',
    'RecognitionApi',
    'Recorder',
    'SFX_DIR',
    'SITE_ICONS',
    'SKIP',
    'Scheduler',
    'Summarizer',
    'VECTOR_SIZE',
    'VectorIndex',
    'answer_refiner',
    'answer_validator',
    'cache_service',
    'faces',
    'geo_location',
    'identity_enrollment',
    'internet_service',
    'is',
    'multimedia',
    'rag_provider',
    'retrieval',
    'scheduler',
    'search_presentation',
    'summarizer'
]
__version__ = '2.0.0'
