# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.router
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tools.vision import HFModel
    from .tools.vision import SF_BLIP_BASE
    from .tools.vision import SF_BLIP_LARGE


_EXPORTS = {
    'HFModel': ('tools.vision', 'HFModel'),
    'SF_BLIP_BASE': ('tools.vision', 'SF_BLIP_BASE'),
    'SF_BLIP_LARGE': ('tools.vision', 'SF_BLIP_LARGE')
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
    'evaluation',
    'tools'
]
__version__ = '2.0.1'
