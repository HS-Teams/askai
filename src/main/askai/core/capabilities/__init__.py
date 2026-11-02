# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.capabilities
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .desktop import AUDIO_SUFFIXES
    from .desktop import ActionResult
    from .desktop import DesktopCapabilities
    from .media_player import MediaPlayer
    from .media_player import PlaybackEnded
    from .desktop import VIDEO_SUFFIXES


_EXPORTS = {
    'AUDIO_SUFFIXES': ('desktop', 'AUDIO_SUFFIXES'),
    'ActionResult': ('desktop', 'ActionResult'),
    'DesktopCapabilities': ('desktop', 'DesktopCapabilities'),
    'MediaPlayer': ('media_player', 'MediaPlayer'),
    'PlaybackEnded': ('media_player', 'PlaybackEnded'),
    'VIDEO_SUFFIXES': ('desktop', 'VIDEO_SUFFIXES')
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
    'AUDIO_SUFFIXES',
    'ActionResult',
    'DesktopCapabilities',
    'MediaPlayer',
    'PlaybackEnded',
    'VIDEO_SUFFIXES',
    'desktop',
    'media_player'
]
__version__ = '2.0.1'
