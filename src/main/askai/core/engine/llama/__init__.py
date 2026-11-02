# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.engine.llama
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .llama_configs import LlamaConfigs
    from .llama_speech import LlamaSpeech
    from .ollama_client import OllamaClient


_EXPORTS = {
    'LlamaConfigs': ('llama_configs', 'LlamaConfigs'),
    'LlamaSpeech': ('llama_speech', 'LlamaSpeech'),
    'OllamaClient': ('ollama_client', 'OllamaClient')
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
    'LlamaConfigs',
    'LlamaSpeech',
    'OllamaClient',
    'llama_configs',
    'llama_speech',
    'ollama_client'
]
__version__ = '2.0.1'
