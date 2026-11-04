# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.support
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .chat_context import ChatContext
    from .communication import CommunicationBus
    from .short_term_memory import Message
    from .persistent_memory import PersistentMemory
    from .communication import ReplyChannel
    from .communication import SESSION_MESSAGES
    from .shared_instances import SharedInstances
    from .short_term_memory import ShortTermMemory
    from .llm_parser import T
    from .usage import Usage


_EXPORTS = {
    'ChatContext': ('chat_context', 'ChatContext'),
    'CommunicationBus': ('communication', 'CommunicationBus'),
    'Message': ('short_term_memory', 'Message'),
    'PersistentMemory': ('persistent_memory', 'PersistentMemory'),
    'ReplyChannel': ('communication', 'ReplyChannel'),
    'SESSION_MESSAGES': ('communication', 'SESSION_MESSAGES'),
    'SharedInstances': ('shared_instances', 'SharedInstances'),
    'ShortTermMemory': ('short_term_memory', 'ShortTermMemory'),
    'T': ('llm_parser', 'T'),
    'Usage': ('usage', 'Usage')
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
    'ChatContext',
    'CommunicationBus',
    'Message',
    'PersistentMemory',
    'ReplyChannel',
    'SESSION_MESSAGES',
    'SharedInstances',
    'ShortTermMemory',
    'T',
    'Usage',
    'app_paths',
    'cache_policy',
    'chat_context',
    'communication',
    'context_usage',
    'inference',
    'llm_parser',
    'markdown_text',
    'number_format',
    'os_utils',
    'performance',
    'persistent_memory',
    'shared_instances',
    'short_term_memory',
    'startup',
    'usage',
    'utilities'
]
__version__ = '2.0.1'
