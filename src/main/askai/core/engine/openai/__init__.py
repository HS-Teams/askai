# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.engine.openai
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .temperature import CHATBOT_RESPONSES
    from .temperature import CODE_COMMENT_GENERATION
    from .temperature import CODE_GENERATION
    from .temperature import COLDEST
    from .temperature import CREATIVE_WRITING
    from .temperature import DATA_ANALYSIS
    from .temperature import DEFAULT
    from .temperature import EXPLORATORY_CODE_WRITING
    from .openai_model import GPT_4
    from .openai_model import GPT_4_1
    from .openai_model import GPT_4_1_MINI
    from .openai_model import GPT_4_1_NANO
    from .openai_model import GPT_4_5
    from .openai_model import GPT_4_O
    from .openai_model import GPT_4_O_MINI
    from .openai_model import GPT_4_TURBO
    from .openai_model import GPT_5
    from .openai_model import GPT_5_1
    from .openai_model import GPT_5_1_CHAT
    from .openai_model import GPT_5_1_MINI
    from .openai_model import GPT_5_1_NANO
    from .openai_model import GPT_5_2
    from .openai_model import GPT_5_2_CHAT
    from .openai_model import GPT_5_2_MINI
    from .openai_model import GPT_5_2_NANO
    from .openai_model import GPT_5_CHAT
    from .openai_model import GPT_5_MINI
    from .openai_model import GPT_5_NANO
    from .temperature import HOTTEST
    from .openai_model import O1
    from .openai_model import O1_MINI
    from .openai_model import O1_PREVIEW
    from .openai_model import O1_PRO
    from .openai_model import O3
    from .openai_model import O3_MINI
    from .openai_model import O3_MINI_HIGH
    from .openai_model import O3_PRO
    from .openai_model import O4_MINI
    from .openai_model import O4_MINI_HIGH
    from .openai_engine import OpenAIEngine
    from .openai_model import OpenAIModel
    from .openai_speech import OpenAISpeech
    from .openai_vision import OpenAIVision
    from .openai_configs import OpenAiConfigs
    from .temperature import Temperature


_EXPORTS = {
    'CHATBOT_RESPONSES': ('temperature', 'CHATBOT_RESPONSES'),
    'CODE_COMMENT_GENERATION': ('temperature', 'CODE_COMMENT_GENERATION'),
    'CODE_GENERATION': ('temperature', 'CODE_GENERATION'),
    'COLDEST': ('temperature', 'COLDEST'),
    'CREATIVE_WRITING': ('temperature', 'CREATIVE_WRITING'),
    'DATA_ANALYSIS': ('temperature', 'DATA_ANALYSIS'),
    'DEFAULT': ('temperature', 'DEFAULT'),
    'EXPLORATORY_CODE_WRITING': ('temperature', 'EXPLORATORY_CODE_WRITING'),
    'GPT_4': ('openai_model', 'GPT_4'),
    'GPT_4_1': ('openai_model', 'GPT_4_1'),
    'GPT_4_1_MINI': ('openai_model', 'GPT_4_1_MINI'),
    'GPT_4_1_NANO': ('openai_model', 'GPT_4_1_NANO'),
    'GPT_4_5': ('openai_model', 'GPT_4_5'),
    'GPT_4_O': ('openai_model', 'GPT_4_O'),
    'GPT_4_O_MINI': ('openai_model', 'GPT_4_O_MINI'),
    'GPT_4_TURBO': ('openai_model', 'GPT_4_TURBO'),
    'GPT_5': ('openai_model', 'GPT_5'),
    'GPT_5_1': ('openai_model', 'GPT_5_1'),
    'GPT_5_1_CHAT': ('openai_model', 'GPT_5_1_CHAT'),
    'GPT_5_1_MINI': ('openai_model', 'GPT_5_1_MINI'),
    'GPT_5_1_NANO': ('openai_model', 'GPT_5_1_NANO'),
    'GPT_5_2': ('openai_model', 'GPT_5_2'),
    'GPT_5_2_CHAT': ('openai_model', 'GPT_5_2_CHAT'),
    'GPT_5_2_MINI': ('openai_model', 'GPT_5_2_MINI'),
    'GPT_5_2_NANO': ('openai_model', 'GPT_5_2_NANO'),
    'GPT_5_CHAT': ('openai_model', 'GPT_5_CHAT'),
    'GPT_5_MINI': ('openai_model', 'GPT_5_MINI'),
    'GPT_5_NANO': ('openai_model', 'GPT_5_NANO'),
    'HOTTEST': ('temperature', 'HOTTEST'),
    'O1': ('openai_model', 'O1'),
    'O1_MINI': ('openai_model', 'O1_MINI'),
    'O1_PREVIEW': ('openai_model', 'O1_PREVIEW'),
    'O1_PRO': ('openai_model', 'O1_PRO'),
    'O3': ('openai_model', 'O3'),
    'O3_MINI': ('openai_model', 'O3_MINI'),
    'O3_MINI_HIGH': ('openai_model', 'O3_MINI_HIGH'),
    'O3_PRO': ('openai_model', 'O3_PRO'),
    'O4_MINI': ('openai_model', 'O4_MINI'),
    'O4_MINI_HIGH': ('openai_model', 'O4_MINI_HIGH'),
    'OpenAIEngine': ('openai_engine', 'OpenAIEngine'),
    'OpenAIModel': ('openai_model', 'OpenAIModel'),
    'OpenAISpeech': ('openai_speech', 'OpenAISpeech'),
    'OpenAIVision': ('openai_vision', 'OpenAIVision'),
    'OpenAiConfigs': ('openai_configs', 'OpenAiConfigs'),
    'Temperature': ('temperature', 'Temperature')
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
    'CHATBOT_RESPONSES',
    'CODE_COMMENT_GENERATION',
    'CODE_GENERATION',
    'COLDEST',
    'CREATIVE_WRITING',
    'DATA_ANALYSIS',
    'DEFAULT',
    'EXPLORATORY_CODE_WRITING',
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
    'OpenAIEngine',
    'OpenAIModel',
    'OpenAISpeech',
    'OpenAIVision',
    'OpenAiConfigs',
    'Temperature',
    'openai_configs',
    'openai_engine',
    'openai_model',
    'openai_speech',
    'openai_vision',
    'temperature'
]
__version__ = '2.0.0'
