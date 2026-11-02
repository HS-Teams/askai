# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.enums
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .run_modes import ASKAI_CLI
    from .run_modes import ASKAI_CMD
    from .run_modes import ASKAI_TUI
    from .acc_color import AccColor
    from .acc_color import BAD
    from .router_mode import CHAT
    from .verbosity import DETAILED
    from .acc_color import EXCELLENT
    from .verbosity import FULL
    from .acc_color import GOOD
    from .acc_color import INTERRUPT
    from .verbosity import LOW
    from .verbosity import MINIMUM
    from .acc_color import MODERATE
    from .verbosity import NORMAL
    from .router_mode import QNA
    from .router_mode import QSTRING
    from .router_mode import RAG
    from .router_mode import RouterMode
    from .run_modes import RunModes
    from .router_mode import TAIUS
    from .acc_color import TERMINATE
    from .verbosity import Verbosity


_EXPORTS = {
    'ASKAI_CLI': ('run_modes', 'ASKAI_CLI'),
    'ASKAI_CMD': ('run_modes', 'ASKAI_CMD'),
    'ASKAI_TUI': ('run_modes', 'ASKAI_TUI'),
    'AccColor': ('acc_color', 'AccColor'),
    'BAD': ('acc_color', 'BAD'),
    'CHAT': ('router_mode', 'CHAT'),
    'DETAILED': ('verbosity', 'DETAILED'),
    'EXCELLENT': ('acc_color', 'EXCELLENT'),
    'FULL': ('verbosity', 'FULL'),
    'GOOD': ('acc_color', 'GOOD'),
    'INTERRUPT': ('acc_color', 'INTERRUPT'),
    'LOW': ('verbosity', 'LOW'),
    'MINIMUM': ('verbosity', 'MINIMUM'),
    'MODERATE': ('acc_color', 'MODERATE'),
    'NORMAL': ('verbosity', 'NORMAL'),
    'QNA': ('router_mode', 'QNA'),
    'QSTRING': ('router_mode', 'QSTRING'),
    'RAG': ('router_mode', 'RAG'),
    'RouterMode': ('router_mode', 'RouterMode'),
    'RunModes': ('run_modes', 'RunModes'),
    'TAIUS': ('router_mode', 'TAIUS'),
    'TERMINATE': ('acc_color', 'TERMINATE'),
    'Verbosity': ('verbosity', 'Verbosity')
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
    'ASKAI_CLI',
    'ASKAI_CMD',
    'ASKAI_TUI',
    'AccColor',
    'BAD',
    'CHAT',
    'DETAILED',
    'EXCELLENT',
    'FULL',
    'GOOD',
    'INTERRUPT',
    'LOW',
    'MINIMUM',
    'MODERATE',
    'NORMAL',
    'QNA',
    'QSTRING',
    'RAG',
    'RouterMode',
    'RunModes',
    'TAIUS',
    'TERMINATE',
    'Verbosity',
    'acc_color',
    'router_mode',
    'run_modes',
    'verbosity'
]
__version__ = '2.0.1'
