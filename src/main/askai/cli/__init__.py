# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.cli
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .answer_renderer import ANSWER_THEME
    from .agent_interaction import AgentInteraction
    from .agent_progress import AgentProgress
    from .playback import CONTROLS
    from .confirmation import Confirmation
    from .playback import FEEDBACK_SECONDS
    from .help_formatter import HELP_THEME
    from .help_formatter import HelpCommand
    from .help_formatter import HelpGroup
    from .listening_indicator import ListeningIndicator
    from .prompt_input import PromptInput


_EXPORTS = {
    'ANSWER_THEME': ('answer_renderer', 'ANSWER_THEME'),
    'AgentInteraction': ('agent_interaction', 'AgentInteraction'),
    'AgentProgress': ('agent_progress', 'AgentProgress'),
    'CONTROLS': ('playback', 'CONTROLS'),
    'Confirmation': ('confirmation', 'Confirmation'),
    'FEEDBACK_SECONDS': ('playback', 'FEEDBACK_SECONDS'),
    'HELP_THEME': ('help_formatter', 'HELP_THEME'),
    'HelpCommand': ('help_formatter', 'HelpCommand'),
    'HelpGroup': ('help_formatter', 'HelpGroup'),
    'ListeningIndicator': ('listening_indicator', 'ListeningIndicator'),
    'PromptInput': ('prompt_input', 'PromptInput')
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
    'ANSWER_THEME',
    'AgentInteraction',
    'AgentProgress',
    'CONTROLS',
    'Confirmation',
    'FEEDBACK_SECONDS',
    'HELP_THEME',
    'HelpCommand',
    'HelpGroup',
    'ListeningIndicator',
    'PromptInput',
    'agent_interaction',
    'agent_progress',
    'answer_renderer',
    'confirmation',
    'dictation_input',
    'help_formatter',
    'interaction_text',
    'listening_indicator',
    'output',
    'playback',
    'prompt_input',
    'speech_renderer',
    'startup_progress',
    'suggestions'
]
__version__ = '2.0.1'
