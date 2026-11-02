# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: test
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .test_main import TEST_DIR
    from .test_main import TestMain


_EXPORTS = {
    'TEST_DIR': ('test_main', 'TEST_DIR'),
    'TestMain': ('test_main', 'TestMain')
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
    'TEST_DIR',
    'TestMain',
    'core',
    'fixtures',
    'test_main'
]
__version__ = '2.0.0'
