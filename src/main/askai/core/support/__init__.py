# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.support
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .text_formatter import CHAT_ICONS
    from .chat_context import ChatContext
    from .communication import CommunicationBus
    from .short_term_memory import Message
    from .persistent_memory import PersistentMemory
    from .text_formatter import RE_MD_CODE_BLOCK
    from .text_formatter import RE_MD_ESCAPES
    from .text_formatter import RE_TYPES
    from .text_formatter import RE_URL
    from .text_formatter import RICH_THEMES
    from .communication import ReplyChannel
    from .communication import SESSION_MESSAGES
    from .shared_instances import SharedInstances
    from .short_term_memory import ShortTermMemory
    from .llm_parser import T
    from .text_formatter import TextFormatter
    from .usage import Usage


_EXPORTS = {
    'CHAT_ICONS': ('text_formatter', 'CHAT_ICONS'),
    'ChatContext': ('chat_context', 'ChatContext'),
    'CommunicationBus': ('communication', 'CommunicationBus'),
    'Message': ('short_term_memory', 'Message'),
    'PersistentMemory': ('persistent_memory', 'PersistentMemory'),
    'RE_MD_CODE_BLOCK': ('text_formatter', 'RE_MD_CODE_BLOCK'),
    'RE_MD_ESCAPES': ('text_formatter', 'RE_MD_ESCAPES'),
    'RE_TYPES': ('text_formatter', 'RE_TYPES'),
    'RE_URL': ('text_formatter', 'RE_URL'),
    'RICH_THEMES': ('text_formatter', 'RICH_THEMES'),
    'ReplyChannel': ('communication', 'ReplyChannel'),
    'SESSION_MESSAGES': ('communication', 'SESSION_MESSAGES'),
    'SharedInstances': ('shared_instances', 'SharedInstances'),
    'ShortTermMemory': ('short_term_memory', 'ShortTermMemory'),
    'T': ('llm_parser', 'T'),
    'TextFormatter': ('text_formatter', 'TextFormatter'),
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
    'CHAT_ICONS',
    'ChatContext',
    'CommunicationBus',
    'Message',
    'PersistentMemory',
    'RE_MD_CODE_BLOCK',
    'RE_MD_ESCAPES',
    'RE_TYPES',
    'RE_URL',
    'RICH_THEMES',
    'ReplyChannel',
    'SESSION_MESSAGES',
    'SharedInstances',
    'ShortTermMemory',
    'T',
    'TextFormatter',
    'Usage',
    'app_paths',
    'cache_policy',
    'chat_context',
    'communication',
    'context_usage',
    'inference',
    'llm_parser',
    'number_format',
    'os_utils',
    'performance',
    'persistent_memory',
    'shared_instances',
    'short_term_memory',
    'startup',
    'text_formatter',
    'usage',
    'utilities'
]
__version__ = '2.0.1'
