# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.model
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_reply import AIReply
    from .acc_response import AccResponse
    from .api_keys import ApiKeys
    from .api_keys import Config
    from .screenshot_result import DocumentModel
    from .image_result import ImageResult
    from .refined_response import RefinedResponse
    from .screenshot_result import ScreenshotResult
    from .search_result import SearchResult
    from .summary_result import SummaryResult
    from .screenshot_result import WebsiteModel


_EXPORTS = {
    'AIReply': ('ai_reply', 'AIReply'),
    'AccResponse': ('acc_response', 'AccResponse'),
    'ApiKeys': ('api_keys', 'ApiKeys'),
    'Config': ('api_keys', 'Config'),
    'DocumentModel': ('screenshot_result', 'DocumentModel'),
    'ImageResult': ('image_result', 'ImageResult'),
    'RefinedResponse': ('refined_response', 'RefinedResponse'),
    'ScreenshotResult': ('screenshot_result', 'ScreenshotResult'),
    'SearchResult': ('search_result', 'SearchResult'),
    'SummaryResult': ('summary_result', 'SummaryResult'),
    'WebsiteModel': ('screenshot_result', 'WebsiteModel')
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
    'AIReply',
    'AccResponse',
    'ApiKeys',
    'Config',
    'DocumentModel',
    'ImageResult',
    'RefinedResponse',
    'ScreenshotResult',
    'SearchResult',
    'SummaryResult',
    'WebsiteModel',
    'acc_response',
    'ai_reply',
    'api_keys',
    'image_result',
    'refined_response',
    'screenshot_result',
    'search_result',
    'summary_result'
]
__version__ = '2.0.1'
