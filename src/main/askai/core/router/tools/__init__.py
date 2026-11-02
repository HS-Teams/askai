# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.router.tools
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .vision import HFModel
    from .vision import SF_BLIP_BASE
    from .vision import SF_BLIP_LARGE


_EXPORTS = {
    'HFModel': ('vision', 'HFModel'),
    'SF_BLIP_BASE': ('vision', 'SF_BLIP_BASE'),
    'SF_BLIP_LARGE': ('vision', 'SF_BLIP_LARGE')
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
    'HFModel',
    'SF_BLIP_BASE',
    'SF_BLIP_LARGE',
    'analysis',
    'browser',
    'general',
    'generation',
    'summarization',
    'terminal',
    'vision'
]
__version__ = '2.0.1'
