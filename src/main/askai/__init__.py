# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: main.askai
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .language.language import AF_ZA
    from .language.ai_translator import AITranslator
    from .cli.answer_renderer import ANSWER_THEME
    from .language.language import AR_AE
    from .language.language import AR_BH
    from .language.language import AR_DZ
    from .language.language import AR_EG
    from .language.language import AR_IQ
    from .language.language import AR_JO
    from .language.language import AR_KW
    from .language.language import AR_LY
    from .language.language import AR_MA
    from .language.language import AR_OM
    from .language.language import AR_QA
    from .language.language import AR_SA
    from .language.language import AR_TN
    from .language.language import AR_YE
    from .core.askai_events import ASKAI_BUS
    from .tui.app_icons import ASSISTIVE_OFF
    from .tui.app_icons import ASSISTIVE_ON
    from .language.language import AS_IN
    from .language.language import AZ_AZ
    from .tui.agent_interaction import AgentInteraction
    from .cli.agent_interaction import AgentInteraction
    from .cli.agent_progress import AgentProgress
    from .tui.app_widgets import AppHelp
    from .tui.app_icons import AppIcons
    from .tui.app_widgets import AppInfo
    from .tui.app_widgets import AppSettings
    from .core.askai import AskAi
    from .tui.askai_app import AskAiApp
    from .core.askai_cli import AskAiCli
    from .core.askai_configs import AskAiConfigs
    from .core.askai_events import AskAiEvents
    from .core.askai_messages import AskAiMessages
    from .core.askai_prompt import AskAiPrompt
    from .core.askai_settings import AskAiSettings
    from .language.language import BE_BY
    from .language.language import BG_BG
    from .tui.askai_app import BINDINGS
    from .tui.agent_interaction import BINDINGS
    from .language.language import BN_IN
    from .gestures.scroll import BOTTOM_LIMIT
    from .language.language import BS_BA
    from .tui.app_icons import BUILT_IN_SPEAKER
    from .language.language import C
    from .tui.app_icons import CACHING_OFF
    from .tui.app_icons import CACHING_ON
    from .gestures.controller import CAMERA_MARGIN
    from .language.language import CA_ES
    from .tui.app_icons import CLOCK
    from .gestures.controller import CLOSE_RATIO
    from .tui.app_icons import CONSOLE
    from .cli.playback import CONTROLS
    from .tui.app_icons import COPY_REPLY
    from .tui.askai_app import CSS_PATH
    from .language.language import CS_CZ
    from .exception.exceptions import CameraAccessFailure
    from .cli.confirmation import Confirmation
    from .language.language import DA_DK
    from .gestures.controller import DEAD_ZONE
    from .tui.app_icons import DEBUG_OFF
    from .tui.app_icons import DEBUG_ON
    from .tui.app_icons import DEFAULT
    from .language.language import DE_AT
    from .language.language import DE_BE
    from .language.language import DE_CH
    from .language.language import DE_DE
    from .language.language import DE_LI
    from .language.language import DE_LU
    from .tui.app_icons import DISLIKE
    from .gestures.controller import DRAG_HOLD_SECONDS
    from .exception.exceptions import DocumentsNotFound
    from .language.language import EL_CY
    from .language.language import EL_GR
    from .tui.askai_app import ENABLE_COMMAND_PALETTE
    from .language.language import EN_AU
    from .language.language import EN_BW
    from .language.language import EN_CA
    from .language.language import EN_GB
    from .language.language import EN_HK
    from .language.language import EN_IE
    from .language.language import EN_IN
    from .language.language import EN_MT
    from .language.language import EN_NZ
    from .language.language import EN_PH
    from .language.language import EN_SG
    from .language.language import EN_US
    from .language.language import EN_ZW
    from .language.language import ES_AR
    from .language.language import ES_BO
    from .language.language import ES_CL
    from .language.language import ES_CO
    from .language.language import ES_CR
    from .language.language import ES_DO
    from .language.language import ES_EC
    from .language.language import ES_ES
    from .language.language import ES_GT
    from .language.language import ES_HN
    from .language.language import ES_MX
    from .language.language import ES_NI
    from .language.language import ES_PA
    from .language.language import ES_PE
    from .language.language import ES_PR
    from .language.language import ES_PY
    from .language.language import ES_SV
    from .language.language import ES_US
    from .language.language import ES_UY
    from .language.language import ES_VE
    from .language.language import ET_EE
    from .tui.app_icons import EXIT
    from .gestures.controller import EXIT_HOLD_SECONDS
    from .gestures.pointer_response import FAST_SPEED
    from .cli.playback import FEEDBACK_SECONDS
    from .gestures.controller import FINE_POINTER_DISTANCE
    from .gestures.controller import FINE_POINTER_MIN_FACTOR
    from .language.language import FI_FI
    from .gestures.thumbs_up import FOLDED_FINGERS
    from .gestures.thumbs_up import FOLDED_RATIO
    from .language.language import FR_BE
    from .language.language import FR_CA
    from .language.language import FR_CH
    from .language.language import FR_FR
    from .language.language import FR_LU
    from .tui.app_icons import GLOBE
    from .gestures.session import GRANTS
    from .language.language import GU_IN
    from .gestures.controller import GestureController
    from .gestures.controller import GestureState
    from .tui.app_icons import HEADPHONES
    from .tui.app_icons import HELP
    from .cli.help_formatter import HELP_THEME
    from .language.language import HE_IL
    from .language.language import HI_IN
    from .language.language import HR_HR
    from .language.language import HU_HU
    from .language.language import HY_AM
    from .gestures.tracker import HandTracker
    from .tui.app_header import Header
    from .tui.app_header import HeaderNotifications
    from .tui.app_header import HeaderTitle
    from .cli.help_formatter import HelpCommand
    from .cli.help_formatter import HelpGroup
    from .language.language import ID_ID
    from .gestures.session import INACTIVITY_SECONDS
    from .tui.app_icons import INFO
    from .gestures.preview import INITIAL_SIZE
    from .language.language import IS_IS
    from .language.language import IT_CH
    from .language.language import IT_IT
    from .exception.exceptions import ImpossibleQuery
    from .exception.exceptions import InaccurateResponse
    from .tui.app_widgets import InputActions
    from .tui.app_widgets import InputArea
    from .tui.app_suggester import InputSuggester
    from .exception.exceptions import IntelligibleAudioError
    from .exception.exceptions import InterruptionRequest
    from .exception.exceptions import InvalidInputDevice
    from .exception.exceptions import InvalidRecognitionApiError
    from .exception.exceptions import InvalidStructuredResponse
    from .language.language import JA_JP
    from .language.language import KA_GE
    from .language.language import KK_KZ
    from .language.language import KN_IN
    from .language.language import KO_KR
    from .language.language import KS_IN
    from .language.language import KU_TR
    from .language.language import KY_KG
    from .gestures.preview import LABELS
    from .tui.app_icons import LIKE
    from .tui.app_icons import LISTENING_OFF
    from .tui.app_icons import LISTENING_ON
    from .language.language import LT_LT
    from .language.language import LV_LV
    from .language.language import Language
    from .cli.listening_indicator import ListeningIndicator
    from .gestures.pointer_response import MAX_FACTOR
    from .gestures.pointer_response import MAX_GAP_SECONDS
    from .gestures.thumbs_up import MAX_HORIZONTAL_RATIO
    from .gestures.scroll import MAX_STEPS
    from .tui.app_icons import MENU
    from .gestures.command import MESSAGES
    from .language.detection import MINIMUM_LANGUAGE_DISTANCE
    from .gestures.pointer_response import MIN_FACTOR
    from .gestures.pointer_response import MIN_SAMPLE_SECONDS
    from .gestures.thumbs_up import MIN_THUMB_HEIGHT_RATIO
    from .language.language import MK_MK
    from .language.language import ML_IN
    from .gestures.tracker import MODEL_URL
    from .language.language import MR_IN
    from .language.language import MS_MY
    from .language.language import MT_MT
    from .exception.exceptions import MaxInteractionsReached
    from .tui.app_widgets import MenuIcon
    from .exception.exceptions import MissingApiKeyError
    from .language.language import NB_NO
    from .gestures.scroll import NEUTRAL_BOTTOM
    from .gestures.scroll import NEUTRAL_TOP
    from .language.language import NL_BE
    from .language.language import NL_NL
    from .language.language import NN_NO
    from .language.detection import NON_PROSE
    from .exception.exceptions import NoSuchEngineError
    from .gestures.controller import OPEN_RATIO
    from .language.language import OR_IN
    from .language.language import PA_IN
    from .language.language import PL_PL
    from .core.askai_prompt import PROMPT_DIR
    from .language.language import PT_BR
    from .language.language import PT_PT
    from .gestures.preview import Pointer
    from .gestures.pointer_response import PointerResponse
    from .gestures.preview import Preview
    from .cli.prompt_input import PromptInput
    from .tui.app_icons import READ_ALOUD
    from .tui.app_icons import REGENERATE
    from .core.askai_configs import RESOURCE_DIR
    from .gestures.pointer_response import RESPONSE_SECONDS
    from .language.language import RO_RO
    from .language.language import RU_RU
    from .language.language import RU_UA
    from .exception.exceptions import RecognitionApiRequestError
    from .language.language import SA_IN
    from .gestures.controller import SCROLL_COOLDOWN_SECONDS
    from .gestures.controller import SCROLL_IDLE_SECONDS
    from .gestures.scroll import SCROLL_INTERVAL
    from .tui.app_icons import SEPARATOR_H
    from .tui.app_icons import SEPARATOR_V
    from .tui.app_icons import SETTINGS
    from .gestures.sfx import SFX_DIR
    from .language.language import SK_SK
    from .language.language import SL_SI
    from .gestures.controller import SMOOTHING
    from .tui.app_icons import SPEAKING_OFF
    from .tui.app_icons import SPEAKING_ON
    from .language.language import SQ_AL
    from .language.language import SR_ME
    from .language.language import SR_RS
    from .tui.app_icons import STARTED
    from .gestures.thumbs_up import STRAIGHT_COSINE
    from .language.language import SV_SE
    from .gestures.scroll import ScrollMotion
    from .tui.app_widgets import Splash
    from .language.language import TA_IN
    from .language.language import TE_IN
    from .language.language import TH_TH
    from .gestures.preview import TITLE
    from .tui.app_icons import TOC
    from .gestures.scroll import TOP_LIMIT
    from .language.language import TR_TR
    from .exception.exceptions import TerminatingQuery
    from .exception.exceptions import TokenLengthExceeded
    from .exception.exceptions import TranslationPackageError
    from .language.language import UK_UA
    from .language.language import VI_VN
    from .core.askai_events import VOICE_INPUT_EVENT
    from .exception.exceptions import WebCamInitializationFailure
    from .language.language import ZH_CN
    from .language.language import ZH_HK
    from .language.language import ZH_SG
    from .language.language import ZH_TW


_EXPORTS = {
    'AF_ZA': ('language.language', 'AF_ZA'),
    'AITranslator': ('language.ai_translator', 'AITranslator'),
    'ANSWER_THEME': ('cli.answer_renderer', 'ANSWER_THEME'),
    'AR_AE': ('language.language', 'AR_AE'),
    'AR_BH': ('language.language', 'AR_BH'),
    'AR_DZ': ('language.language', 'AR_DZ'),
    'AR_EG': ('language.language', 'AR_EG'),
    'AR_IQ': ('language.language', 'AR_IQ'),
    'AR_JO': ('language.language', 'AR_JO'),
    'AR_KW': ('language.language', 'AR_KW'),
    'AR_LY': ('language.language', 'AR_LY'),
    'AR_MA': ('language.language', 'AR_MA'),
    'AR_OM': ('language.language', 'AR_OM'),
    'AR_QA': ('language.language', 'AR_QA'),
    'AR_SA': ('language.language', 'AR_SA'),
    'AR_TN': ('language.language', 'AR_TN'),
    'AR_YE': ('language.language', 'AR_YE'),
    'ASKAI_BUS': ('core.askai_events', 'ASKAI_BUS'),
    'ASSISTIVE_OFF': ('tui.app_icons', 'ASSISTIVE_OFF'),
    'ASSISTIVE_ON': ('tui.app_icons', 'ASSISTIVE_ON'),
    'AS_IN': ('language.language', 'AS_IN'),
    'AZ_AZ': ('language.language', 'AZ_AZ'),
    'AgentInteraction': ('tui.agent_interaction', 'AgentInteraction'),
    'AgentInteraction': ('cli.agent_interaction', 'AgentInteraction'),
    'AgentProgress': ('cli.agent_progress', 'AgentProgress'),
    'AppHelp': ('tui.app_widgets', 'AppHelp'),
    'AppIcons': ('tui.app_icons', 'AppIcons'),
    'AppInfo': ('tui.app_widgets', 'AppInfo'),
    'AppSettings': ('tui.app_widgets', 'AppSettings'),
    'AskAi': ('core.askai', 'AskAi'),
    'AskAiApp': ('tui.askai_app', 'AskAiApp'),
    'AskAiCli': ('core.askai_cli', 'AskAiCli'),
    'AskAiConfigs': ('core.askai_configs', 'AskAiConfigs'),
    'AskAiEvents': ('core.askai_events', 'AskAiEvents'),
    'AskAiMessages': ('core.askai_messages', 'AskAiMessages'),
    'AskAiPrompt': ('core.askai_prompt', 'AskAiPrompt'),
    'AskAiSettings': ('core.askai_settings', 'AskAiSettings'),
    'BE_BY': ('language.language', 'BE_BY'),
    'BG_BG': ('language.language', 'BG_BG'),
    'BINDINGS': ('tui.askai_app', 'BINDINGS'),
    'BINDINGS': ('tui.agent_interaction', 'BINDINGS'),
    'BN_IN': ('language.language', 'BN_IN'),
    'BOTTOM_LIMIT': ('gestures.scroll', 'BOTTOM_LIMIT'),
    'BS_BA': ('language.language', 'BS_BA'),
    'BUILT_IN_SPEAKER': ('tui.app_icons', 'BUILT_IN_SPEAKER'),
    'C': ('language.language', 'C'),
    'CACHING_OFF': ('tui.app_icons', 'CACHING_OFF'),
    'CACHING_ON': ('tui.app_icons', 'CACHING_ON'),
    'CAMERA_MARGIN': ('gestures.controller', 'CAMERA_MARGIN'),
    'CA_ES': ('language.language', 'CA_ES'),
    'CLOCK': ('tui.app_icons', 'CLOCK'),
    'CLOSE_RATIO': ('gestures.controller', 'CLOSE_RATIO'),
    'CONSOLE': ('tui.app_icons', 'CONSOLE'),
    'CONTROLS': ('cli.playback', 'CONTROLS'),
    'COPY_REPLY': ('tui.app_icons', 'COPY_REPLY'),
    'CSS_PATH': ('tui.askai_app', 'CSS_PATH'),
    'CS_CZ': ('language.language', 'CS_CZ'),
    'CameraAccessFailure': ('exception.exceptions', 'CameraAccessFailure'),
    'Confirmation': ('cli.confirmation', 'Confirmation'),
    'DA_DK': ('language.language', 'DA_DK'),
    'DEAD_ZONE': ('gestures.controller', 'DEAD_ZONE'),
    'DEBUG_OFF': ('tui.app_icons', 'DEBUG_OFF'),
    'DEBUG_ON': ('tui.app_icons', 'DEBUG_ON'),
    'DEFAULT': ('tui.app_icons', 'DEFAULT'),
    'DE_AT': ('language.language', 'DE_AT'),
    'DE_BE': ('language.language', 'DE_BE'),
    'DE_CH': ('language.language', 'DE_CH'),
    'DE_DE': ('language.language', 'DE_DE'),
    'DE_LI': ('language.language', 'DE_LI'),
    'DE_LU': ('language.language', 'DE_LU'),
    'DISLIKE': ('tui.app_icons', 'DISLIKE'),
    'DRAG_HOLD_SECONDS': ('gestures.controller', 'DRAG_HOLD_SECONDS'),
    'DocumentsNotFound': ('exception.exceptions', 'DocumentsNotFound'),
    'EL_CY': ('language.language', 'EL_CY'),
    'EL_GR': ('language.language', 'EL_GR'),
    'ENABLE_COMMAND_PALETTE': ('tui.askai_app', 'ENABLE_COMMAND_PALETTE'),
    'EN_AU': ('language.language', 'EN_AU'),
    'EN_BW': ('language.language', 'EN_BW'),
    'EN_CA': ('language.language', 'EN_CA'),
    'EN_GB': ('language.language', 'EN_GB'),
    'EN_HK': ('language.language', 'EN_HK'),
    'EN_IE': ('language.language', 'EN_IE'),
    'EN_IN': ('language.language', 'EN_IN'),
    'EN_MT': ('language.language', 'EN_MT'),
    'EN_NZ': ('language.language', 'EN_NZ'),
    'EN_PH': ('language.language', 'EN_PH'),
    'EN_SG': ('language.language', 'EN_SG'),
    'EN_US': ('language.language', 'EN_US'),
    'EN_ZW': ('language.language', 'EN_ZW'),
    'ES_AR': ('language.language', 'ES_AR'),
    'ES_BO': ('language.language', 'ES_BO'),
    'ES_CL': ('language.language', 'ES_CL'),
    'ES_CO': ('language.language', 'ES_CO'),
    'ES_CR': ('language.language', 'ES_CR'),
    'ES_DO': ('language.language', 'ES_DO'),
    'ES_EC': ('language.language', 'ES_EC'),
    'ES_ES': ('language.language', 'ES_ES'),
    'ES_GT': ('language.language', 'ES_GT'),
    'ES_HN': ('language.language', 'ES_HN'),
    'ES_MX': ('language.language', 'ES_MX'),
    'ES_NI': ('language.language', 'ES_NI'),
    'ES_PA': ('language.language', 'ES_PA'),
    'ES_PE': ('language.language', 'ES_PE'),
    'ES_PR': ('language.language', 'ES_PR'),
    'ES_PY': ('language.language', 'ES_PY'),
    'ES_SV': ('language.language', 'ES_SV'),
    'ES_US': ('language.language', 'ES_US'),
    'ES_UY': ('language.language', 'ES_UY'),
    'ES_VE': ('language.language', 'ES_VE'),
    'ET_EE': ('language.language', 'ET_EE'),
    'EXIT': ('tui.app_icons', 'EXIT'),
    'EXIT_HOLD_SECONDS': ('gestures.controller', 'EXIT_HOLD_SECONDS'),
    'FAST_SPEED': ('gestures.pointer_response', 'FAST_SPEED'),
    'FEEDBACK_SECONDS': ('cli.playback', 'FEEDBACK_SECONDS'),
    'FINE_POINTER_DISTANCE': ('gestures.controller', 'FINE_POINTER_DISTANCE'),
    'FINE_POINTER_MIN_FACTOR': ('gestures.controller', 'FINE_POINTER_MIN_FACTOR'),
    'FI_FI': ('language.language', 'FI_FI'),
    'FOLDED_FINGERS': ('gestures.thumbs_up', 'FOLDED_FINGERS'),
    'FOLDED_RATIO': ('gestures.thumbs_up', 'FOLDED_RATIO'),
    'FR_BE': ('language.language', 'FR_BE'),
    'FR_CA': ('language.language', 'FR_CA'),
    'FR_CH': ('language.language', 'FR_CH'),
    'FR_FR': ('language.language', 'FR_FR'),
    'FR_LU': ('language.language', 'FR_LU'),
    'GLOBE': ('tui.app_icons', 'GLOBE'),
    'GRANTS': ('gestures.session', 'GRANTS'),
    'GU_IN': ('language.language', 'GU_IN'),
    'GestureController': ('gestures.controller', 'GestureController'),
    'GestureState': ('gestures.controller', 'GestureState'),
    'HEADPHONES': ('tui.app_icons', 'HEADPHONES'),
    'HELP': ('tui.app_icons', 'HELP'),
    'HELP_THEME': ('cli.help_formatter', 'HELP_THEME'),
    'HE_IL': ('language.language', 'HE_IL'),
    'HI_IN': ('language.language', 'HI_IN'),
    'HR_HR': ('language.language', 'HR_HR'),
    'HU_HU': ('language.language', 'HU_HU'),
    'HY_AM': ('language.language', 'HY_AM'),
    'HandTracker': ('gestures.tracker', 'HandTracker'),
    'Header': ('tui.app_header', 'Header'),
    'HeaderNotifications': ('tui.app_header', 'HeaderNotifications'),
    'HeaderTitle': ('tui.app_header', 'HeaderTitle'),
    'HelpCommand': ('cli.help_formatter', 'HelpCommand'),
    'HelpGroup': ('cli.help_formatter', 'HelpGroup'),
    'ID_ID': ('language.language', 'ID_ID'),
    'INACTIVITY_SECONDS': ('gestures.session', 'INACTIVITY_SECONDS'),
    'INFO': ('tui.app_icons', 'INFO'),
    'INITIAL_SIZE': ('gestures.preview', 'INITIAL_SIZE'),
    'IS_IS': ('language.language', 'IS_IS'),
    'IT_CH': ('language.language', 'IT_CH'),
    'IT_IT': ('language.language', 'IT_IT'),
    'ImpossibleQuery': ('exception.exceptions', 'ImpossibleQuery'),
    'InaccurateResponse': ('exception.exceptions', 'InaccurateResponse'),
    'InputActions': ('tui.app_widgets', 'InputActions'),
    'InputArea': ('tui.app_widgets', 'InputArea'),
    'InputSuggester': ('tui.app_suggester', 'InputSuggester'),
    'IntelligibleAudioError': ('exception.exceptions', 'IntelligibleAudioError'),
    'InterruptionRequest': ('exception.exceptions', 'InterruptionRequest'),
    'InvalidInputDevice': ('exception.exceptions', 'InvalidInputDevice'),
    'InvalidRecognitionApiError': ('exception.exceptions', 'InvalidRecognitionApiError'),
    'InvalidStructuredResponse': ('exception.exceptions', 'InvalidStructuredResponse'),
    'JA_JP': ('language.language', 'JA_JP'),
    'KA_GE': ('language.language', 'KA_GE'),
    'KK_KZ': ('language.language', 'KK_KZ'),
    'KN_IN': ('language.language', 'KN_IN'),
    'KO_KR': ('language.language', 'KO_KR'),
    'KS_IN': ('language.language', 'KS_IN'),
    'KU_TR': ('language.language', 'KU_TR'),
    'KY_KG': ('language.language', 'KY_KG'),
    'LABELS': ('gestures.preview', 'LABELS'),
    'LIKE': ('tui.app_icons', 'LIKE'),
    'LISTENING_OFF': ('tui.app_icons', 'LISTENING_OFF'),
    'LISTENING_ON': ('tui.app_icons', 'LISTENING_ON'),
    'LT_LT': ('language.language', 'LT_LT'),
    'LV_LV': ('language.language', 'LV_LV'),
    'Language': ('language.language', 'Language'),
    'ListeningIndicator': ('cli.listening_indicator', 'ListeningIndicator'),
    'MAX_FACTOR': ('gestures.pointer_response', 'MAX_FACTOR'),
    'MAX_GAP_SECONDS': ('gestures.pointer_response', 'MAX_GAP_SECONDS'),
    'MAX_HORIZONTAL_RATIO': ('gestures.thumbs_up', 'MAX_HORIZONTAL_RATIO'),
    'MAX_STEPS': ('gestures.scroll', 'MAX_STEPS'),
    'MENU': ('tui.app_icons', 'MENU'),
    'MESSAGES': ('gestures.command', 'MESSAGES'),
    'MINIMUM_LANGUAGE_DISTANCE': ('language.detection', 'MINIMUM_LANGUAGE_DISTANCE'),
    'MIN_FACTOR': ('gestures.pointer_response', 'MIN_FACTOR'),
    'MIN_SAMPLE_SECONDS': ('gestures.pointer_response', 'MIN_SAMPLE_SECONDS'),
    'MIN_THUMB_HEIGHT_RATIO': ('gestures.thumbs_up', 'MIN_THUMB_HEIGHT_RATIO'),
    'MK_MK': ('language.language', 'MK_MK'),
    'ML_IN': ('language.language', 'ML_IN'),
    'MODEL_URL': ('gestures.tracker', 'MODEL_URL'),
    'MR_IN': ('language.language', 'MR_IN'),
    'MS_MY': ('language.language', 'MS_MY'),
    'MT_MT': ('language.language', 'MT_MT'),
    'MaxInteractionsReached': ('exception.exceptions', 'MaxInteractionsReached'),
    'MenuIcon': ('tui.app_widgets', 'MenuIcon'),
    'MissingApiKeyError': ('exception.exceptions', 'MissingApiKeyError'),
    'NB_NO': ('language.language', 'NB_NO'),
    'NEUTRAL_BOTTOM': ('gestures.scroll', 'NEUTRAL_BOTTOM'),
    'NEUTRAL_TOP': ('gestures.scroll', 'NEUTRAL_TOP'),
    'NL_BE': ('language.language', 'NL_BE'),
    'NL_NL': ('language.language', 'NL_NL'),
    'NN_NO': ('language.language', 'NN_NO'),
    'NON_PROSE': ('language.detection', 'NON_PROSE'),
    'NoSuchEngineError': ('exception.exceptions', 'NoSuchEngineError'),
    'OPEN_RATIO': ('gestures.controller', 'OPEN_RATIO'),
    'OR_IN': ('language.language', 'OR_IN'),
    'PA_IN': ('language.language', 'PA_IN'),
    'PL_PL': ('language.language', 'PL_PL'),
    'PROMPT_DIR': ('core.askai_prompt', 'PROMPT_DIR'),
    'PT_BR': ('language.language', 'PT_BR'),
    'PT_PT': ('language.language', 'PT_PT'),
    'Pointer': ('gestures.preview', 'Pointer'),
    'PointerResponse': ('gestures.pointer_response', 'PointerResponse'),
    'Preview': ('gestures.preview', 'Preview'),
    'PromptInput': ('cli.prompt_input', 'PromptInput'),
    'READ_ALOUD': ('tui.app_icons', 'READ_ALOUD'),
    'REGENERATE': ('tui.app_icons', 'REGENERATE'),
    'RESOURCE_DIR': ('core.askai_configs', 'RESOURCE_DIR'),
    'RESPONSE_SECONDS': ('gestures.pointer_response', 'RESPONSE_SECONDS'),
    'RO_RO': ('language.language', 'RO_RO'),
    'RU_RU': ('language.language', 'RU_RU'),
    'RU_UA': ('language.language', 'RU_UA'),
    'RecognitionApiRequestError': ('exception.exceptions', 'RecognitionApiRequestError'),
    'SA_IN': ('language.language', 'SA_IN'),
    'SCROLL_COOLDOWN_SECONDS': ('gestures.controller', 'SCROLL_COOLDOWN_SECONDS'),
    'SCROLL_IDLE_SECONDS': ('gestures.controller', 'SCROLL_IDLE_SECONDS'),
    'SCROLL_INTERVAL': ('gestures.scroll', 'SCROLL_INTERVAL'),
    'SEPARATOR_H': ('tui.app_icons', 'SEPARATOR_H'),
    'SEPARATOR_V': ('tui.app_icons', 'SEPARATOR_V'),
    'SETTINGS': ('tui.app_icons', 'SETTINGS'),
    'SFX_DIR': ('gestures.sfx', 'SFX_DIR'),
    'SK_SK': ('language.language', 'SK_SK'),
    'SL_SI': ('language.language', 'SL_SI'),
    'SMOOTHING': ('gestures.controller', 'SMOOTHING'),
    'SPEAKING_OFF': ('tui.app_icons', 'SPEAKING_OFF'),
    'SPEAKING_ON': ('tui.app_icons', 'SPEAKING_ON'),
    'SQ_AL': ('language.language', 'SQ_AL'),
    'SR_ME': ('language.language', 'SR_ME'),
    'SR_RS': ('language.language', 'SR_RS'),
    'STARTED': ('tui.app_icons', 'STARTED'),
    'STRAIGHT_COSINE': ('gestures.thumbs_up', 'STRAIGHT_COSINE'),
    'SV_SE': ('language.language', 'SV_SE'),
    'ScrollMotion': ('gestures.scroll', 'ScrollMotion'),
    'Splash': ('tui.app_widgets', 'Splash'),
    'TA_IN': ('language.language', 'TA_IN'),
    'TE_IN': ('language.language', 'TE_IN'),
    'TH_TH': ('language.language', 'TH_TH'),
    'TITLE': ('gestures.preview', 'TITLE'),
    'TOC': ('tui.app_icons', 'TOC'),
    'TOP_LIMIT': ('gestures.scroll', 'TOP_LIMIT'),
    'TR_TR': ('language.language', 'TR_TR'),
    'TerminatingQuery': ('exception.exceptions', 'TerminatingQuery'),
    'TokenLengthExceeded': ('exception.exceptions', 'TokenLengthExceeded'),
    'TranslationPackageError': ('exception.exceptions', 'TranslationPackageError'),
    'UK_UA': ('language.language', 'UK_UA'),
    'VI_VN': ('language.language', 'VI_VN'),
    'VOICE_INPUT_EVENT': ('core.askai_events', 'VOICE_INPUT_EVENT'),
    'WebCamInitializationFailure': ('exception.exceptions', 'WebCamInitializationFailure'),
    'ZH_CN': ('language.language', 'ZH_CN'),
    'ZH_HK': ('language.language', 'ZH_HK'),
    'ZH_SG': ('language.language', 'ZH_SG'),
    'ZH_TW': ('language.language', 'ZH_TW')
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
    'AF_ZA',
    'AITranslator',
    'ANSWER_THEME',
    'AR_AE',
    'AR_BH',
    'AR_DZ',
    'AR_EG',
    'AR_IQ',
    'AR_JO',
    'AR_KW',
    'AR_LY',
    'AR_MA',
    'AR_OM',
    'AR_QA',
    'AR_SA',
    'AR_TN',
    'AR_YE',
    'ASKAI_BUS',
    'ASSISTIVE_OFF',
    'ASSISTIVE_ON',
    'AS_IN',
    'AZ_AZ',
    'AgentInteraction',
    'AgentInteraction',
    'AgentProgress',
    'AppHelp',
    'AppIcons',
    'AppInfo',
    'AppSettings',
    'AskAi',
    'AskAiApp',
    'AskAiCli',
    'AskAiConfigs',
    'AskAiEvents',
    'AskAiMessages',
    'AskAiPrompt',
    'AskAiSettings',
    'BE_BY',
    'BG_BG',
    'BINDINGS',
    'BINDINGS',
    'BN_IN',
    'BOTTOM_LIMIT',
    'BS_BA',
    'BUILT_IN_SPEAKER',
    'C',
    'CACHING_OFF',
    'CACHING_ON',
    'CAMERA_MARGIN',
    'CA_ES',
    'CLOCK',
    'CLOSE_RATIO',
    'CONSOLE',
    'CONTROLS',
    'COPY_REPLY',
    'CSS_PATH',
    'CS_CZ',
    'CameraAccessFailure',
    'Confirmation',
    'DA_DK',
    'DEAD_ZONE',
    'DEBUG_OFF',
    'DEBUG_ON',
    'DEFAULT',
    'DE_AT',
    'DE_BE',
    'DE_CH',
    'DE_DE',
    'DE_LI',
    'DE_LU',
    'DISLIKE',
    'DRAG_HOLD_SECONDS',
    'DocumentsNotFound',
    'EL_CY',
    'EL_GR',
    'ENABLE_COMMAND_PALETTE',
    'EN_AU',
    'EN_BW',
    'EN_CA',
    'EN_GB',
    'EN_HK',
    'EN_IE',
    'EN_IN',
    'EN_MT',
    'EN_NZ',
    'EN_PH',
    'EN_SG',
    'EN_US',
    'EN_ZW',
    'ES_AR',
    'ES_BO',
    'ES_CL',
    'ES_CO',
    'ES_CR',
    'ES_DO',
    'ES_EC',
    'ES_ES',
    'ES_GT',
    'ES_HN',
    'ES_MX',
    'ES_NI',
    'ES_PA',
    'ES_PE',
    'ES_PR',
    'ES_PY',
    'ES_SV',
    'ES_US',
    'ES_UY',
    'ES_VE',
    'ET_EE',
    'EXIT',
    'EXIT_HOLD_SECONDS',
    'FAST_SPEED',
    'FEEDBACK_SECONDS',
    'FINE_POINTER_DISTANCE',
    'FINE_POINTER_MIN_FACTOR',
    'FI_FI',
    'FOLDED_FINGERS',
    'FOLDED_RATIO',
    'FR_BE',
    'FR_CA',
    'FR_CH',
    'FR_FR',
    'FR_LU',
    'GLOBE',
    'GRANTS',
    'GU_IN',
    'GestureController',
    'GestureState',
    'HEADPHONES',
    'HELP',
    'HELP_THEME',
    'HE_IL',
    'HI_IN',
    'HR_HR',
    'HU_HU',
    'HY_AM',
    'HandTracker',
    'Header',
    'HeaderNotifications',
    'HeaderTitle',
    'HelpCommand',
    'HelpGroup',
    'ID_ID',
    'INACTIVITY_SECONDS',
    'INFO',
    'INITIAL_SIZE',
    'IS_IS',
    'IT_CH',
    'IT_IT',
    'ImpossibleQuery',
    'InaccurateResponse',
    'InputActions',
    'InputArea',
    'InputSuggester',
    'IntelligibleAudioError',
    'InterruptionRequest',
    'InvalidInputDevice',
    'InvalidRecognitionApiError',
    'InvalidStructuredResponse',
    'JA_JP',
    'KA_GE',
    'KK_KZ',
    'KN_IN',
    'KO_KR',
    'KS_IN',
    'KU_TR',
    'KY_KG',
    'LABELS',
    'LIKE',
    'LISTENING_OFF',
    'LISTENING_ON',
    'LT_LT',
    'LV_LV',
    'Language',
    'ListeningIndicator',
    'MAX_FACTOR',
    'MAX_GAP_SECONDS',
    'MAX_HORIZONTAL_RATIO',
    'MAX_STEPS',
    'MENU',
    'MESSAGES',
    'MINIMUM_LANGUAGE_DISTANCE',
    'MIN_FACTOR',
    'MIN_SAMPLE_SECONDS',
    'MIN_THUMB_HEIGHT_RATIO',
    'MK_MK',
    'ML_IN',
    'MODEL_URL',
    'MR_IN',
    'MS_MY',
    'MT_MT',
    'MaxInteractionsReached',
    'MenuIcon',
    'MissingApiKeyError',
    'NB_NO',
    'NEUTRAL_BOTTOM',
    'NEUTRAL_TOP',
    'NL_BE',
    'NL_NL',
    'NN_NO',
    'NON_PROSE',
    'NoSuchEngineError',
    'OPEN_RATIO',
    'OR_IN',
    'PA_IN',
    'PL_PL',
    'PROMPT_DIR',
    'PT_BR',
    'PT_PT',
    'Pointer',
    'PointerResponse',
    'Preview',
    'PromptInput',
    'READ_ALOUD',
    'REGENERATE',
    'RESOURCE_DIR',
    'RESPONSE_SECONDS',
    'RO_RO',
    'RU_RU',
    'RU_UA',
    'RecognitionApiRequestError',
    'SA_IN',
    'SCROLL_COOLDOWN_SECONDS',
    'SCROLL_IDLE_SECONDS',
    'SCROLL_INTERVAL',
    'SEPARATOR_H',
    'SEPARATOR_V',
    'SETTINGS',
    'SFX_DIR',
    'SK_SK',
    'SL_SI',
    'SMOOTHING',
    'SPEAKING_OFF',
    'SPEAKING_ON',
    'SQ_AL',
    'SR_ME',
    'SR_RS',
    'STARTED',
    'STRAIGHT_COSINE',
    'SV_SE',
    'ScrollMotion',
    'Splash',
    'TA_IN',
    'TE_IN',
    'TH_TH',
    'TITLE',
    'TOC',
    'TOP_LIMIT',
    'TR_TR',
    'TerminatingQuery',
    'TokenLengthExceeded',
    'TranslationPackageError',
    'UK_UA',
    'VI_VN',
    'VOICE_INPUT_EVENT',
    'WebCamInitializationFailure',
    'ZH_CN',
    'ZH_HK',
    'ZH_SG',
    'ZH_TW',
    'cli',
    'core',
    'exception',
    'gestures',
    'language',
    'mcp_server',
    'tui'
]
__version__ = '2.0.0'
