# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.component.faces
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import DEFAULT_THRESHOLD
    from .models import DetectedFace
    from .selections import FaceAction
    from .index import FaceIndex
    from .models import FaceModels
    from .index import FaceRecord
    from .selections import FaceSelection
    from .selections import MAX_IDENTITY_NAME
    from .selections import MERGE
    from .migration import MIGRATION_KEY
    from .models import MODEL_FILES
    from .models import MODEL_VERSION
    from .selections import NEW
    from .selections import REPLACE
    from .selections import SKIP
    from .models import VECTOR_SIZE


_EXPORTS = {
    'DEFAULT_THRESHOLD': ('models', 'DEFAULT_THRESHOLD'),
    'DetectedFace': ('models', 'DetectedFace'),
    'FaceAction': ('selections', 'FaceAction'),
    'FaceIndex': ('index', 'FaceIndex'),
    'FaceModels': ('models', 'FaceModels'),
    'FaceRecord': ('index', 'FaceRecord'),
    'FaceSelection': ('selections', 'FaceSelection'),
    'MAX_IDENTITY_NAME': ('selections', 'MAX_IDENTITY_NAME'),
    'MERGE': ('selections', 'MERGE'),
    'MIGRATION_KEY': ('migration', 'MIGRATION_KEY'),
    'MODEL_FILES': ('models', 'MODEL_FILES'),
    'MODEL_VERSION': ('models', 'MODEL_VERSION'),
    'NEW': ('selections', 'NEW'),
    'REPLACE': ('selections', 'REPLACE'),
    'SKIP': ('selections', 'SKIP'),
    'VECTOR_SIZE': ('models', 'VECTOR_SIZE')
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
    'DEFAULT_THRESHOLD',
    'DetectedFace',
    'FaceAction',
    'FaceIndex',
    'FaceModels',
    'FaceRecord',
    'FaceSelection',
    'MAX_IDENTITY_NAME',
    'MERGE',
    'MIGRATION_KEY',
    'MODEL_FILES',
    'MODEL_VERSION',
    'NEW',
    'REPLACE',
    'SKIP',
    'VECTOR_SIZE',
    'index',
    'migration',
    'models',
    'selections',
    'service'
]
__version__ = '2.0.0'
