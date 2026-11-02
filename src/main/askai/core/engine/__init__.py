# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.engine
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ai_engine import AIEngine
    from .ai_model import AIModel
    from .ai_vision import AIVision
    from .agent.agent_engine import AgentEngine
    from .openai.temperature import CHATBOT_RESPONSES
    from .openai.temperature import CODE_COMMENT_GENERATION
    from .openai.temperature import CODE_GENERATION
    from .openai.temperature import COLDEST
    from .openai.temperature import CREATIVE_WRITING
    from .openai.temperature import DATA_ANALYSIS
    from .openai.temperature import DEFAULT
    from .runtime import ENGINES
    from .openai.temperature import EXPLORATORY_CODE_WRITING
    from .engine_factory import EngineFactory
    from .openai.openai_model import GPT_4
    from .openai.openai_model import GPT_4_1
    from .openai.openai_model import GPT_4_1_MINI
    from .openai.openai_model import GPT_4_1_NANO
    from .openai.openai_model import GPT_4_5
    from .openai.openai_model import GPT_4_O
    from .openai.openai_model import GPT_4_O_MINI
    from .openai.openai_model import GPT_4_TURBO
    from .openai.openai_model import GPT_5
    from .openai.openai_model import GPT_5_1
    from .openai.openai_model import GPT_5_1_CHAT
    from .openai.openai_model import GPT_5_1_MINI
    from .openai.openai_model import GPT_5_1_NANO
    from .openai.openai_model import GPT_5_2
    from .openai.openai_model import GPT_5_2_CHAT
    from .openai.openai_model import GPT_5_2_MINI
    from .openai.openai_model import GPT_5_2_NANO
    from .openai.openai_model import GPT_5_CHAT
    from .openai.openai_model import GPT_5_MINI
    from .openai.openai_model import GPT_5_NANO
    from .openai.temperature import HOTTEST
    from .inference import Inference
    from .llama.llama_configs import LlamaConfigs
    from .llama.llama_speech import LlamaSpeech
    from .openai.openai_model import O1
    from .openai.openai_model import O1_MINI
    from .openai.openai_model import O1_PREVIEW
    from .openai.openai_model import O1_PRO
    from .openai.openai_model import O3
    from .openai.openai_model import O3_MINI
    from .openai.openai_model import O3_MINI_HIGH
    from .openai.openai_model import O3_PRO
    from .openai.openai_model import O4_MINI
    from .openai.openai_model import O4_MINI_HIGH
    from .llama.ollama_client import OllamaClient
    from .openai.openai_engine import OpenAIEngine
    from .openai.openai_model import OpenAIModel
    from .openai.openai_speech import OpenAISpeech
    from .openai.openai_vision import OpenAIVision
    from .openai.openai_configs import OpenAiConfigs
    from .runtime import RuntimeEngines
    from .openai.temperature import Temperature


_EXPORTS = {
    'AIEngine': ('ai_engine', 'AIEngine'),
    'AIModel': ('ai_model', 'AIModel'),
    'AIVision': ('ai_vision', 'AIVision'),
    'AgentEngine': ('agent.agent_engine', 'AgentEngine'),
    'CHATBOT_RESPONSES': ('openai.temperature', 'CHATBOT_RESPONSES'),
    'CODE_COMMENT_GENERATION': ('openai.temperature', 'CODE_COMMENT_GENERATION'),
    'CODE_GENERATION': ('openai.temperature', 'CODE_GENERATION'),
    'COLDEST': ('openai.temperature', 'COLDEST'),
    'CREATIVE_WRITING': ('openai.temperature', 'CREATIVE_WRITING'),
    'DATA_ANALYSIS': ('openai.temperature', 'DATA_ANALYSIS'),
    'DEFAULT': ('openai.temperature', 'DEFAULT'),
    'ENGINES': ('runtime', 'ENGINES'),
    'EXPLORATORY_CODE_WRITING': ('openai.temperature', 'EXPLORATORY_CODE_WRITING'),
    'EngineFactory': ('engine_factory', 'EngineFactory'),
    'GPT_4': ('openai.openai_model', 'GPT_4'),
    'GPT_4_1': ('openai.openai_model', 'GPT_4_1'),
    'GPT_4_1_MINI': ('openai.openai_model', 'GPT_4_1_MINI'),
    'GPT_4_1_NANO': ('openai.openai_model', 'GPT_4_1_NANO'),
    'GPT_4_5': ('openai.openai_model', 'GPT_4_5'),
    'GPT_4_O': ('openai.openai_model', 'GPT_4_O'),
    'GPT_4_O_MINI': ('openai.openai_model', 'GPT_4_O_MINI'),
    'GPT_4_TURBO': ('openai.openai_model', 'GPT_4_TURBO'),
    'GPT_5': ('openai.openai_model', 'GPT_5'),
    'GPT_5_1': ('openai.openai_model', 'GPT_5_1'),
    'GPT_5_1_CHAT': ('openai.openai_model', 'GPT_5_1_CHAT'),
    'GPT_5_1_MINI': ('openai.openai_model', 'GPT_5_1_MINI'),
    'GPT_5_1_NANO': ('openai.openai_model', 'GPT_5_1_NANO'),
    'GPT_5_2': ('openai.openai_model', 'GPT_5_2'),
    'GPT_5_2_CHAT': ('openai.openai_model', 'GPT_5_2_CHAT'),
    'GPT_5_2_MINI': ('openai.openai_model', 'GPT_5_2_MINI'),
    'GPT_5_2_NANO': ('openai.openai_model', 'GPT_5_2_NANO'),
    'GPT_5_CHAT': ('openai.openai_model', 'GPT_5_CHAT'),
    'GPT_5_MINI': ('openai.openai_model', 'GPT_5_MINI'),
    'GPT_5_NANO': ('openai.openai_model', 'GPT_5_NANO'),
    'HOTTEST': ('openai.temperature', 'HOTTEST'),
    'Inference': ('inference', 'Inference'),
    'LlamaConfigs': ('llama.llama_configs', 'LlamaConfigs'),
    'LlamaSpeech': ('llama.llama_speech', 'LlamaSpeech'),
    'O1': ('openai.openai_model', 'O1'),
    'O1_MINI': ('openai.openai_model', 'O1_MINI'),
    'O1_PREVIEW': ('openai.openai_model', 'O1_PREVIEW'),
    'O1_PRO': ('openai.openai_model', 'O1_PRO'),
    'O3': ('openai.openai_model', 'O3'),
    'O3_MINI': ('openai.openai_model', 'O3_MINI'),
    'O3_MINI_HIGH': ('openai.openai_model', 'O3_MINI_HIGH'),
    'O3_PRO': ('openai.openai_model', 'O3_PRO'),
    'O4_MINI': ('openai.openai_model', 'O4_MINI'),
    'O4_MINI_HIGH': ('openai.openai_model', 'O4_MINI_HIGH'),
    'OllamaClient': ('llama.ollama_client', 'OllamaClient'),
    'OpenAIEngine': ('openai.openai_engine', 'OpenAIEngine'),
    'OpenAIModel': ('openai.openai_model', 'OpenAIModel'),
    'OpenAISpeech': ('openai.openai_speech', 'OpenAISpeech'),
    'OpenAIVision': ('openai.openai_vision', 'OpenAIVision'),
    'OpenAiConfigs': ('openai.openai_configs', 'OpenAiConfigs'),
    'RuntimeEngines': ('runtime', 'RuntimeEngines'),
    'Temperature': ('openai.temperature', 'Temperature')
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
    'AIEngine',
    'AIModel',
    'AIVision',
    'AgentEngine',
    'CHATBOT_RESPONSES',
    'CODE_COMMENT_GENERATION',
    'CODE_GENERATION',
    'COLDEST',
    'CREATIVE_WRITING',
    'DATA_ANALYSIS',
    'DEFAULT',
    'ENGINES',
    'EXPLORATORY_CODE_WRITING',
    'EngineFactory',
    'GPT_4',
    'GPT_4_1',
    'GPT_4_1_MINI',
    'GPT_4_1_NANO',
    'GPT_4_5',
    'GPT_4_O',
    'GPT_4_O_MINI',
    'GPT_4_TURBO',
    'GPT_5',
    'GPT_5_1',
    'GPT_5_1_CHAT',
    'GPT_5_1_MINI',
    'GPT_5_1_NANO',
    'GPT_5_2',
    'GPT_5_2_CHAT',
    'GPT_5_2_MINI',
    'GPT_5_2_NANO',
    'GPT_5_CHAT',
    'GPT_5_MINI',
    'GPT_5_NANO',
    'HOTTEST',
    'Inference',
    'LlamaConfigs',
    'LlamaSpeech',
    'O1',
    'O1_MINI',
    'O1_PREVIEW',
    'O1_PRO',
    'O3',
    'O3_MINI',
    'O3_MINI_HIGH',
    'O3_PRO',
    'O4_MINI',
    'O4_MINI_HIGH',
    'OllamaClient',
    'OpenAIEngine',
    'OpenAIModel',
    'OpenAISpeech',
    'OpenAIVision',
    'OpenAiConfigs',
    'RuntimeEngines',
    'Temperature',
    'agent',
    'ai_engine',
    'ai_model',
    'ai_vision',
    'engine_factory',
    'inference',
    'llama',
    'openai',
    'runtime'
]
__version__ = '2.0.0'
