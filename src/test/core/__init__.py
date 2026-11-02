# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: test.core
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .support.test_app_paths import AppPathTests
    from .support.test_cache_policy import CachePolicyTests
    from .support.test_communication import CommunicationTests
    from .support.test_number_format import CompactCountTests
    from .support.test_context_capacity import ContextCapacityTests
    from .support.test_history_storage_policy import HistoryStorageTests
    from .support.test_llm_parser import ListParserTests
    from .support.test_parallel_startup import StartupTests
    from .model.test_acc_response import TEST_DIR
    from .support.test_utilities import TestClass
    from .model.test_acc_response import TestClass


_EXPORTS = {
    'AppPathTests': ('support.test_app_paths', 'AppPathTests'),
    'CachePolicyTests': ('support.test_cache_policy', 'CachePolicyTests'),
    'CommunicationTests': ('support.test_communication', 'CommunicationTests'),
    'CompactCountTests': ('support.test_number_format', 'CompactCountTests'),
    'ContextCapacityTests': ('support.test_context_capacity', 'ContextCapacityTests'),
    'HistoryStorageTests': ('support.test_history_storage_policy', 'HistoryStorageTests'),
    'ListParserTests': ('support.test_llm_parser', 'ListParserTests'),
    'StartupTests': ('support.test_parallel_startup', 'StartupTests'),
    'TEST_DIR': ('model.test_acc_response', 'TEST_DIR'),
    'TestClass': ('support.test_utilities', 'TestClass'),
    'TestClass': ('model.test_acc_response', 'TestClass')
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
    'TEST_DIR',
    'TestClass',
    'TestClass',
    'model',
    'support'
]
__version__ = '2.0.1'
