# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.component.multimedia
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .audio_player import AudioPlayer
    from .camera import Camera
    from .recorder import GOOGLE
    from .recorder import OPEN_AI
    from .recorder import RecognitionApi
    from .recorder import Recorder
    from .audio_player import SFX_DIR


_EXPORTS = {
    'AudioPlayer': ('audio_player', 'AudioPlayer'),
    'Camera': ('camera', 'Camera'),
    'GOOGLE': ('recorder', 'GOOGLE'),
    'OPEN_AI': ('recorder', 'OPEN_AI'),
    'RecognitionApi': ('recorder', 'RecognitionApi'),
    'Recorder': ('recorder', 'Recorder'),
    'SFX_DIR': ('audio_player', 'SFX_DIR')
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
    'AudioPlayer',
    'Camera',
    'GOOGLE',
    'OPEN_AI',
    'RecognitionApi',
    'Recorder',
    'SFX_DIR',
    'audio_player',
    'camera',
    'recorder',
    'screenshot'
]
__version__ = '2.0.1'
