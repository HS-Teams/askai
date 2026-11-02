# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.exception
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .exceptions import CameraAccessFailure
    from .exceptions import DocumentsNotFound
    from .exceptions import ImpossibleQuery
    from .exceptions import InaccurateResponse
    from .exceptions import IntelligibleAudioError
    from .exceptions import InterruptionRequest
    from .exceptions import InvalidInputDevice
    from .exceptions import InvalidRecognitionApiError
    from .exceptions import InvalidStructuredResponse
    from .exceptions import MaxInteractionsReached
    from .exceptions import MissingApiKeyError
    from .exceptions import NoSuchEngineError
    from .exceptions import RecognitionApiRequestError
    from .exceptions import TerminatingQuery
    from .exceptions import TokenLengthExceeded
    from .exceptions import TranslationPackageError
    from .exceptions import WebCamInitializationFailure


_EXPORTS = {
    'CameraAccessFailure': ('exceptions', 'CameraAccessFailure'),
    'DocumentsNotFound': ('exceptions', 'DocumentsNotFound'),
    'ImpossibleQuery': ('exceptions', 'ImpossibleQuery'),
    'InaccurateResponse': ('exceptions', 'InaccurateResponse'),
    'IntelligibleAudioError': ('exceptions', 'IntelligibleAudioError'),
    'InterruptionRequest': ('exceptions', 'InterruptionRequest'),
    'InvalidInputDevice': ('exceptions', 'InvalidInputDevice'),
    'InvalidRecognitionApiError': ('exceptions', 'InvalidRecognitionApiError'),
    'InvalidStructuredResponse': ('exceptions', 'InvalidStructuredResponse'),
    'MaxInteractionsReached': ('exceptions', 'MaxInteractionsReached'),
    'MissingApiKeyError': ('exceptions', 'MissingApiKeyError'),
    'NoSuchEngineError': ('exceptions', 'NoSuchEngineError'),
    'RecognitionApiRequestError': ('exceptions', 'RecognitionApiRequestError'),
    'TerminatingQuery': ('exceptions', 'TerminatingQuery'),
    'TokenLengthExceeded': ('exceptions', 'TokenLengthExceeded'),
    'TranslationPackageError': ('exceptions', 'TranslationPackageError'),
    'WebCamInitializationFailure': ('exceptions', 'WebCamInitializationFailure')
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
    'CameraAccessFailure',
    'DocumentsNotFound',
    'ImpossibleQuery',
    'InaccurateResponse',
    'IntelligibleAudioError',
    'InterruptionRequest',
    'InvalidInputDevice',
    'InvalidRecognitionApiError',
    'InvalidStructuredResponse',
    'MaxInteractionsReached',
    'MissingApiKeyError',
    'NoSuchEngineError',
    'RecognitionApiRequestError',
    'TerminatingQuery',
    'TokenLengthExceeded',
    'TranslationPackageError',
    'WebCamInitializationFailure',
    'exceptions'
]
__version__ = '2.0.0'
