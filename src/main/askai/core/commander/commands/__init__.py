# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.commander.commands
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .cache_cmd import CacheCmd
    from .camera_cmd import CameraCmd
    from .general_cmd import GeneralCmd
    from .grants_cmd import GrantsCmd
    from .history_cmd import HistoryCmd
    from .settings_cmd import SettingsCmd
    from .tts_stt_cmd import TtsSttCmd
    from .usage_cmd import UsageCmd


_EXPORTS = {
    'CacheCmd': ('cache_cmd', 'CacheCmd'),
    'CameraCmd': ('camera_cmd', 'CameraCmd'),
    'GeneralCmd': ('general_cmd', 'GeneralCmd'),
    'GrantsCmd': ('grants_cmd', 'GrantsCmd'),
    'HistoryCmd': ('history_cmd', 'HistoryCmd'),
    'SettingsCmd': ('settings_cmd', 'SettingsCmd'),
    'TtsSttCmd': ('tts_stt_cmd', 'TtsSttCmd'),
    'UsageCmd': ('usage_cmd', 'UsageCmd')
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
    'CacheCmd',
    'CameraCmd',
    'GeneralCmd',
    'GrantsCmd',
    'HistoryCmd',
    'SettingsCmd',
    'TtsSttCmd',
    'UsageCmd',
    'cache_cmd',
    'camera_cmd',
    'general_cmd',
    'grants_cmd',
    'history_cmd',
    'settings_cmd',
    'tts_stt_cmd',
    'usage_cmd'
]
__version__ = '2.0.1'
