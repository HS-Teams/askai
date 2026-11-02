# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.language.translators
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .argos_translator import ArgosTranslator
    from .deepl_translator import DeepLTranslator
    from .marian_translator import MODEL_NAME
    from .marian_translator import MarianTranslator


_EXPORTS = {
    'ArgosTranslator': ('argos_translator', 'ArgosTranslator'),
    'DeepLTranslator': ('deepl_translator', 'DeepLTranslator'),
    'MODEL_NAME': ('marian_translator', 'MODEL_NAME'),
    'MarianTranslator': ('marian_translator', 'MarianTranslator')
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
    'ArgosTranslator',
    'DeepLTranslator',
    'MODEL_NAME',
    'MarianTranslator',
    'argos_translator',
    'deepl_translator',
    'marian_translator'
]
__version__ = '2.0.0'
