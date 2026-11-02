# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.processors
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_processor import AIProcessor
    from .chat import ChatProcessor
    from .qstring import NonInteractive
    from .qna import QnA
    from .rag import Rag
    from .taius import TaiusProcessor


_EXPORTS = {
    'AIProcessor': ('ai_processor', 'AIProcessor'),
    'ChatProcessor': ('chat', 'ChatProcessor'),
    'NonInteractive': ('qstring', 'NonInteractive'),
    'QnA': ('qna', 'QnA'),
    'Rag': ('rag', 'Rag'),
    'TaiusProcessor': ('taius', 'TaiusProcessor')
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
    'AIProcessor',
    'ChatProcessor',
    'NonInteractive',
    'QnA',
    'Rag',
    'TaiusProcessor',
    'ai_processor',
    'chat',
    'qna',
    'qstring',
    'rag',
    'taius'
]
__version__ = '2.0.0'
