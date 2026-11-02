# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai.core.agents
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .factory import AGENT_NAMES
    from .contracts import AgentBackend
    from .contracts import AgentError
    from .contracts import AgentEvent
    from .contracts import AgentResult
    from .contracts import AgentTask
    from .camera_tool import CAMERA_TOOL
    from .command_tool import COMMAND_TOOL
    from .codex import CodexBackend
    from .codex_connections import CodexConnections
    from .command_tool import DEFERRED_COMMANDS
    from .elicitation import ELICITATION_METHOD
    from .enrollment_tool import ENROLLMENT_TOOL
    from .elicitation import FORM_MODES
    from .identification_tool import IDENTIFICATION_TOOL
    from .elicitation import INPUT_FORM_METHOD
    from .input_context import MAX_INPUT_CHARS
    from .reasoning_summaries import ReasoningSummaries
    from .screenshot_tool import SCREENSHOT_TOOL
    from .stdio_transport import StdioTransport


_EXPORTS = {
    'AGENT_NAMES': ('factory', 'AGENT_NAMES'),
    'AgentBackend': ('contracts', 'AgentBackend'),
    'AgentError': ('contracts', 'AgentError'),
    'AgentEvent': ('contracts', 'AgentEvent'),
    'AgentResult': ('contracts', 'AgentResult'),
    'AgentTask': ('contracts', 'AgentTask'),
    'CAMERA_TOOL': ('camera_tool', 'CAMERA_TOOL'),
    'COMMAND_TOOL': ('command_tool', 'COMMAND_TOOL'),
    'CodexBackend': ('codex', 'CodexBackend'),
    'CodexConnections': ('codex_connections', 'CodexConnections'),
    'DEFERRED_COMMANDS': ('command_tool', 'DEFERRED_COMMANDS'),
    'ELICITATION_METHOD': ('elicitation', 'ELICITATION_METHOD'),
    'ENROLLMENT_TOOL': ('enrollment_tool', 'ENROLLMENT_TOOL'),
    'FORM_MODES': ('elicitation', 'FORM_MODES'),
    'IDENTIFICATION_TOOL': ('identification_tool', 'IDENTIFICATION_TOOL'),
    'INPUT_FORM_METHOD': ('elicitation', 'INPUT_FORM_METHOD'),
    'MAX_INPUT_CHARS': ('input_context', 'MAX_INPUT_CHARS'),
    'ReasoningSummaries': ('reasoning_summaries', 'ReasoningSummaries'),
    'SCREENSHOT_TOOL': ('screenshot_tool', 'SCREENSHOT_TOOL'),
    'StdioTransport': ('stdio_transport', 'StdioTransport')
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
    'AGENT_NAMES',
    'AgentBackend',
    'AgentError',
    'AgentEvent',
    'AgentResult',
    'AgentTask',
    'CAMERA_TOOL',
    'COMMAND_TOOL',
    'CodexBackend',
    'CodexConnections',
    'DEFERRED_COMMANDS',
    'ELICITATION_METHOD',
    'ENROLLMENT_TOOL',
    'FORM_MODES',
    'IDENTIFICATION_TOOL',
    'INPUT_FORM_METHOD',
    'MAX_INPUT_CHARS',
    'ReasoningSummaries',
    'SCREENSHOT_TOOL',
    'StdioTransport',
    'camera_tool',
    'codex',
    'codex_connections',
    'command_tool',
    'compaction',
    'contracts',
    'desktop_tools',
    'elicitation',
    'enrollment_tool',
    'factory',
    'identification_tool',
    'input_context',
    'model_context',
    'reasoning_summaries',
    'screenshot_tool',
    'stdio_transport'
]
__version__ = '2.0.0'
