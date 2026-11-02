# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: test.core.support
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .test_app_paths import AppPathTests
    from .test_cache_policy import CachePolicyTests
    from .test_communication import CommunicationTests
    from .test_number_format import CompactCountTests
    from .test_context_capacity import ContextCapacityTests
    from .test_history_storage_policy import HistoryStorageTests
    from .test_llm_parser import ListParserTests
    from .test_parallel_startup import StartupTests
    from .test_utilities import TestClass


_EXPORTS = {
    'AppPathTests': ('test_app_paths', 'AppPathTests'),
    'CachePolicyTests': ('test_cache_policy', 'CachePolicyTests'),
    'CommunicationTests': ('test_communication', 'CommunicationTests'),
    'CompactCountTests': ('test_number_format', 'CompactCountTests'),
    'ContextCapacityTests': ('test_context_capacity', 'ContextCapacityTests'),
    'HistoryStorageTests': ('test_history_storage_policy', 'HistoryStorageTests'),
    'ListParserTests': ('test_llm_parser', 'ListParserTests'),
    'StartupTests': ('test_parallel_startup', 'StartupTests'),
    'TestClass': ('test_utilities', 'TestClass')
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
    'AppPathTests',
    'CachePolicyTests',
    'CommunicationTests',
    'CompactCountTests',
    'ContextCapacityTests',
    'HistoryStorageTests',
    'ListParserTests',
    'StartupTests',
    'TestClass',
    'test_app_paths',
    'test_cache_policy',
    'test_communication',
    'test_context_capacity',
    'test_history_storage_policy',
    'test_llm_parser',
    'test_number_format',
    'test_parallel_startup',
    'test_utilities'
]
__version__ = '2.0.0'
