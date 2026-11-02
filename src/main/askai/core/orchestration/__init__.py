# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.orchestration
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .orchestrator import Orchestrator


_EXPORTS = {
    'Orchestrator': ('orchestrator', 'Orchestrator')
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
    'Orchestrator',
    'orchestrator',
    'session_compaction',
    'session_reset'
]
__version__ = '2.0.0'
