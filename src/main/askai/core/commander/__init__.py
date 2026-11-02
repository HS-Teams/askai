# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.commander
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .commander import COMMANDER_HELP_TPL
    from .commands.cache_cmd import CacheCmd
    from .commands.camera_cmd import CameraCmd
    from .commands.general_cmd import GeneralCmd
    from .commands.grants_cmd import GrantsCmd
    from .commands.history_cmd import HistoryCmd
    from .command_results import MAX_OUTPUT
    from .command_results import MAX_RESULTS
    from .commands.settings_cmd import SettingsCmd
    from .commands.tts_stt_cmd import TtsSttCmd
    from .commands.usage_cmd import UsageCmd
    from .command_results import _CommandOutput


_EXPORTS = {
    'COMMANDER_HELP_TPL': ('commander', 'COMMANDER_HELP_TPL'),
    'CacheCmd': ('commands.cache_cmd', 'CacheCmd'),
    'CameraCmd': ('commands.camera_cmd', 'CameraCmd'),
    'GeneralCmd': ('commands.general_cmd', 'GeneralCmd'),
    'GrantsCmd': ('commands.grants_cmd', 'GrantsCmd'),
    'HistoryCmd': ('commands.history_cmd', 'HistoryCmd'),
    'MAX_OUTPUT': ('command_results', 'MAX_OUTPUT'),
    'MAX_RESULTS': ('command_results', 'MAX_RESULTS'),
    'SettingsCmd': ('commands.settings_cmd', 'SettingsCmd'),
    'TtsSttCmd': ('commands.tts_stt_cmd', 'TtsSttCmd'),
    'UsageCmd': ('commands.usage_cmd', 'UsageCmd'),
    '_CommandOutput': ('command_results', '_CommandOutput')
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
    'COMMANDER_HELP_TPL',
    'CacheCmd',
    'CameraCmd',
    'GeneralCmd',
    'GrantsCmd',
    'HistoryCmd',
    'MAX_OUTPUT',
    'MAX_RESULTS',
    'SettingsCmd',
    'TtsSttCmd',
    'UsageCmd',
    '_CommandOutput',
    'agent_commands',
    'command_args',
    'command_results',
    'commander',
    'commands'
]
__version__ = '2.0.0'
