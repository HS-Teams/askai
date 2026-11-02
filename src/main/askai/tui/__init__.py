# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.tui
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app_icons import ASSISTIVE_OFF
    from .app_icons import ASSISTIVE_ON
    from .agent_interaction import AgentInteraction
    from .app_widgets import AppHelp
    from .app_icons import AppIcons
    from .app_widgets import AppInfo
    from .app_widgets import AppSettings
    from .askai_app import AskAiApp
    from .askai_app import BINDINGS
    from .agent_interaction import BINDINGS
    from .app_icons import BUILT_IN_SPEAKER
    from .app_icons import CACHING_OFF
    from .app_icons import CACHING_ON
    from .app_icons import CLOCK
    from .app_icons import CONSOLE
    from .app_icons import COPY_REPLY
    from .askai_app import CSS_PATH
    from .app_icons import DEBUG_OFF
    from .app_icons import DEBUG_ON
    from .app_icons import DEFAULT
    from .app_icons import DISLIKE
    from .askai_app import ENABLE_COMMAND_PALETTE
    from .app_icons import EXIT
    from .app_icons import GLOBE
    from .app_icons import HEADPHONES
    from .app_icons import HELP
    from .app_header import Header
    from .app_header import HeaderNotifications
    from .app_header import HeaderTitle
    from .app_icons import INFO
    from .app_widgets import InputActions
    from .app_widgets import InputArea
    from .app_suggester import InputSuggester
    from .app_icons import LIKE
    from .app_icons import LISTENING_OFF
    from .app_icons import LISTENING_ON
    from .app_icons import MENU
    from .app_widgets import MenuIcon
    from .app_icons import READ_ALOUD
    from .app_icons import REGENERATE
    from .app_icons import SEPARATOR_H
    from .app_icons import SEPARATOR_V
    from .app_icons import SETTINGS
    from .app_icons import SPEAKING_OFF
    from .app_icons import SPEAKING_ON
    from .app_icons import STARTED
    from .app_widgets import Splash
    from .app_icons import TOC


_EXPORTS = {
    'ASSISTIVE_OFF': ('app_icons', 'ASSISTIVE_OFF'),
    'ASSISTIVE_ON': ('app_icons', 'ASSISTIVE_ON'),
    'AgentInteraction': ('agent_interaction', 'AgentInteraction'),
    'AppHelp': ('app_widgets', 'AppHelp'),
    'AppIcons': ('app_icons', 'AppIcons'),
    'AppInfo': ('app_widgets', 'AppInfo'),
    'AppSettings': ('app_widgets', 'AppSettings'),
    'AskAiApp': ('askai_app', 'AskAiApp'),
    'BINDINGS': ('askai_app', 'BINDINGS'),
    'BINDINGS': ('agent_interaction', 'BINDINGS'),
    'BUILT_IN_SPEAKER': ('app_icons', 'BUILT_IN_SPEAKER'),
    'CACHING_OFF': ('app_icons', 'CACHING_OFF'),
    'CACHING_ON': ('app_icons', 'CACHING_ON'),
    'CLOCK': ('app_icons', 'CLOCK'),
    'CONSOLE': ('app_icons', 'CONSOLE'),
    'COPY_REPLY': ('app_icons', 'COPY_REPLY'),
    'CSS_PATH': ('askai_app', 'CSS_PATH'),
    'DEBUG_OFF': ('app_icons', 'DEBUG_OFF'),
    'DEBUG_ON': ('app_icons', 'DEBUG_ON'),
    'DEFAULT': ('app_icons', 'DEFAULT'),
    'DISLIKE': ('app_icons', 'DISLIKE'),
    'ENABLE_COMMAND_PALETTE': ('askai_app', 'ENABLE_COMMAND_PALETTE'),
    'EXIT': ('app_icons', 'EXIT'),
    'GLOBE': ('app_icons', 'GLOBE'),
    'HEADPHONES': ('app_icons', 'HEADPHONES'),
    'HELP': ('app_icons', 'HELP'),
    'Header': ('app_header', 'Header'),
    'HeaderNotifications': ('app_header', 'HeaderNotifications'),
    'HeaderTitle': ('app_header', 'HeaderTitle'),
    'INFO': ('app_icons', 'INFO'),
    'InputActions': ('app_widgets', 'InputActions'),
    'InputArea': ('app_widgets', 'InputArea'),
    'InputSuggester': ('app_suggester', 'InputSuggester'),
    'LIKE': ('app_icons', 'LIKE'),
    'LISTENING_OFF': ('app_icons', 'LISTENING_OFF'),
    'LISTENING_ON': ('app_icons', 'LISTENING_ON'),
    'MENU': ('app_icons', 'MENU'),
    'MenuIcon': ('app_widgets', 'MenuIcon'),
    'READ_ALOUD': ('app_icons', 'READ_ALOUD'),
    'REGENERATE': ('app_icons', 'REGENERATE'),
    'SEPARATOR_H': ('app_icons', 'SEPARATOR_H'),
    'SEPARATOR_V': ('app_icons', 'SEPARATOR_V'),
    'SETTINGS': ('app_icons', 'SETTINGS'),
    'SPEAKING_OFF': ('app_icons', 'SPEAKING_OFF'),
    'SPEAKING_ON': ('app_icons', 'SPEAKING_ON'),
    'STARTED': ('app_icons', 'STARTED'),
    'Splash': ('app_widgets', 'Splash'),
    'TOC': ('app_icons', 'TOC')
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
    'ASSISTIVE_OFF',
    'ASSISTIVE_ON',
    'AgentInteraction',
    'AppHelp',
    'AppIcons',
    'AppInfo',
    'AppSettings',
    'AskAiApp',
    'BINDINGS',
    'BINDINGS',
    'BUILT_IN_SPEAKER',
    'CACHING_OFF',
    'CACHING_ON',
    'CLOCK',
    'CONSOLE',
    'COPY_REPLY',
    'CSS_PATH',
    'DEBUG_OFF',
    'DEBUG_ON',
    'DEFAULT',
    'DISLIKE',
    'ENABLE_COMMAND_PALETTE',
    'EXIT',
    'GLOBE',
    'HEADPHONES',
    'HELP',
    'Header',
    'HeaderNotifications',
    'HeaderTitle',
    'INFO',
    'InputActions',
    'InputArea',
    'InputSuggester',
    'LIKE',
    'LISTENING_OFF',
    'LISTENING_ON',
    'MENU',
    'MenuIcon',
    'READ_ALOUD',
    'REGENERATE',
    'SEPARATOR_H',
    'SEPARATOR_V',
    'SETTINGS',
    'SPEAKING_OFF',
    'SPEAKING_ON',
    'STARTED',
    'Splash',
    'TOC',
    'agent_interaction',
    'app_header',
    'app_icons',
    'app_suggester',
    'app_widgets',
    'askai_app'
]
__version__ = '2.0.1'
