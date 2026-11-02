# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.permissions
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .grants import ALLOW
    from .grants import ASK
    from .grants import DENY
    from .grants import GRANTS
    from .grants import GrantDenied
    from .grants import GrantPolicy
    from .grants import GrantValue
    from .grants import NEVER
    from .grants import PREFIX


_EXPORTS = {
    'ALLOW': ('grants', 'ALLOW'),
    'ASK': ('grants', 'ASK'),
    'DENY': ('grants', 'DENY'),
    'GRANTS': ('grants', 'GRANTS'),
    'GrantDenied': ('grants', 'GrantDenied'),
    'GrantPolicy': ('grants', 'GrantPolicy'),
    'GrantValue': ('grants', 'GrantValue'),
    'NEVER': ('grants', 'NEVER'),
    'PREFIX': ('grants', 'PREFIX')
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
    'ALLOW',
    'ASK',
    'DENY',
    'GRANTS',
    'GrantDenied',
    'GrantPolicy',
    'GrantValue',
    'NEVER',
    'PREFIX',
    'computer_use',
    'grants'
]
__version__ = '2.0.0'
