# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agents.factory import AGENT_NAMES
    from .engine.ai_engine import AIEngine
    from .engine.ai_model import AIModel
    from .processors.ai_processor import AIProcessor
    from .model.ai_reply import AIReply
    from .engine.ai_vision import AIVision
    from .permissions.grants import ALLOW
    from .permissions.grants import ASK
    from .askai_events import ASKAI_BUS
    from .enums.run_modes import ASKAI_CLI
    from .enums.run_modes import ASKAI_CMD
    from .component.internet_service import ASKAI_INTERNET_DATA_KEY
    from .enums.run_modes import ASKAI_TUI
    from .capabilities.desktop import AUDIO_SUFFIXES
    from .speech.audio_tags import AUDIO_TAG
    from .enums.acc_color import AccColor
    from .model.acc_response import AccResponse
    from .capabilities.desktop import ActionResult
    from .agents.contracts import AgentBackend
    from .agents.contracts import AgentError
    from .agents.contracts import AgentEvent
    from .agents.contracts import AgentResult
    from .agents.contracts import AgentTask
    from .model.api_keys import ApiKeys
    from .askai import AskAi
    from .askai_cli import AskAiCli
    from .askai_configs import AskAiConfigs
    from .askai_events import AskAiEvents
    from .askai_messages import AskAiMessages
    from .askai_prompt import AskAiPrompt
    from .askai_settings import AskAiSettings
    from .component.answer_validator import Assessment
    from .enums.acc_color import BAD
    from .agents.camera_tool import CAMERA_TOOL
    from .component.internet_service import CATEGORY_ICONS
    from .component.search_presentation import CATEGORY_ICONS
    from .enums.router_mode import CHAT
    from .support.text_formatter import CHAT_ICONS
    from .commander.commander import COMMANDER_HELP_TPL
    from .agents.command_tool import COMMAND_TOOL
    from .component.cache_service import CacheService
    from .support.chat_context import ChatContext
    from .processors.chat import ChatProcessor
    from .agents.codex import CodexBackend
    from .agents.codex_connections import CodexConnections
    from .speech.codex_tts import CodexTTS
    from .support.communication import CommunicationBus
    from .model.api_keys import Config
    from .agents.command_tool import DEFERRED_COMMANDS
    from .permissions.grants import DENY
    from .enums.verbosity import DETAILED
    from .capabilities.desktop import DesktopCapabilities
    from .component.retrieval import Document
    from .model.screenshot_result import DocumentModel
    from .agents.elicitation import ELICITATION_METHOD
    from .speech.dictation import END_SILENCE_SECONDS
    from .engine.runtime import ENGINES
    from .agents.enrollment_tool import ENROLLMENT_TOOL
    from .enums.acc_color import EXCELLENT
    from .speech.elevenlabs_tts import ElevenLabsTTS
    from .engine.engine_factory import EngineFactory
    from .component.identity_enrollment import EnrollmentFace
    from .component.identity_enrollment import EnrollmentPhoto
    from .agents.elicitation import FORM_MODES
    from .enums.verbosity import FULL
    from .speech.fallback_tts import FallbackTTS
    from .enums.acc_color import GOOD
    from .permissions.grants import GRANTS
    from .component.geo_location import GeoLocation
    from .permissions.grants import GrantDenied
    from .permissions.grants import GrantPolicy
    from .permissions.grants import GrantValue
    from .agents.identification_tool import IDENTIFICATION_TOOL
    from .agents.elicitation import INPUT_FORM_METHOD
    from .enums.acc_color import INTERRUPT
    from .component.identity_enrollment import IdentityEnrollment
    from .model.image_result import ImageResult
    from .engine.inference import Inference
    from .component.internet_service import InternetService
    from .enums.verbosity import LOW
    from .agents.input_context import MAX_INPUT_CHARS
    from .commander.command_results import MAX_OUTPUT
    from .speech.output_queue import MAX_PENDING
    from .commander.command_results import MAX_RESULTS
    from .enums.verbosity import MINIMUM
    from .speech.capture import MIN_SPEECH_WAIT_SECONDS
    from .enums.acc_color import MODERATE
    from .capabilities.media_player import MediaPlayer
    from .support.short_term_memory import Message
    from .speech.presentation import NARRATION_PREFIX
    from .permissions.grants import NEVER
    from .enums.verbosity import NORMAL
    from .speech.narration import Narration
    from .processors.qstring import NonInteractive
    from .orchestration.orchestrator import Orchestrator
    from .permissions.grants import PREFIX
    from .speech.codex_tts import PROBE_TEXT
    from .speech.elevenlabs_tts import PROBE_TEXT
    from .askai_prompt import PROMPT_DIR
    from .support.persistent_memory import PersistentMemory
    from .capabilities.media_player import PlaybackEnded
    from .speech.timing import PlaybackTiming
    from .enums.router_mode import QNA
    from .enums.router_mode import QSTRING
    from .processors.qna import QnA
    from .enums.router_mode import RAG
    from .component.rag_provider import RAGProvider
    from .speech.dictation import REFINEMENT_SCHEMA
    from .askai_configs import RESOURCE_DIR
    from .support.text_formatter import RE_MD_CODE_BLOCK
    from .support.text_formatter import RE_MD_ESCAPES
    from .support.text_formatter import RE_TYPES
    from .support.text_formatter import RE_URL
    from .support.text_formatter import RICH_THEMES
    from .processors.rag import Rag
    from .agents.reasoning_summaries import ReasoningSummaries
    from .speech.recognizer_stt import RecognizerSTT
    from .model.refined_response import RefinedResponse
    from .support.communication import ReplyChannel
    from .enums.router_mode import RouterMode
    from .enums.run_modes import RunModes
    from .engine.runtime import RuntimeEngines
    from .speech.elevenlabs_tts import SAMPLE_RATE
    from .agents.screenshot_tool import SCREENSHOT_TOOL
    from .support.communication import SESSION_MESSAGES
    from .component.internet_service import SITE_ICONS
    from .speech.contracts import STTEngine
    from .component.scheduler import Scheduler
    from .model.screenshot_result import ScreenshotResult
    from .model.search_result import SearchResult
    from .support.shared_instances import SharedInstances
    from .support.short_term_memory import ShortTermMemory
    from .speech.output_queue import SpeechOutputQueue
    from .speech.service import SpeechService
    from .speech.pcm_stream import StartedSpeechError
    from .agents.stdio_transport import StdioTransport
    from .component.summarizer import Summarizer
    from .model.summary_result import SummaryResult
    from .support.llm_parser import T
    from .enums.router_mode import TAIUS
    from .enums.acc_color import TERMINATE
    from .speech.contracts import TTSEngine
    from .processors.taius import TaiusProcessor
    from .support.text_formatter import TextFormatter
    from .support.usage import Usage
    from .capabilities.desktop import VIDEO_SUFFIXES
    from .askai_events import VOICE_INPUT_EVENT
    from .component.retrieval import VectorIndex
    from .enums.verbosity import Verbosity
    from .speech.recognizer_stt import WHISPER_CONTROL_TOKEN
    from .speech.recognizer_stt import WHISPER_LOGPROB_THRESHOLD
    from .model.screenshot_result import WebsiteModel
    from .commander.command_results import _CommandOutput
    from .speech.capture import _FinishableStream


_EXPORTS = {
    'AGENT_NAMES': ('agents.factory', 'AGENT_NAMES'),
    'AIEngine': ('engine.ai_engine', 'AIEngine'),
    'AIModel': ('engine.ai_model', 'AIModel'),
    'AIProcessor': ('processors.ai_processor', 'AIProcessor'),
    'AIReply': ('model.ai_reply', 'AIReply'),
    'AIVision': ('engine.ai_vision', 'AIVision'),
    'ALLOW': ('permissions.grants', 'ALLOW'),
    'ASK': ('permissions.grants', 'ASK'),
    'ASKAI_BUS': ('askai_events', 'ASKAI_BUS'),
    'ASKAI_CLI': ('enums.run_modes', 'ASKAI_CLI'),
    'ASKAI_CMD': ('enums.run_modes', 'ASKAI_CMD'),
    'ASKAI_INTERNET_DATA_KEY': ('component.internet_service', 'ASKAI_INTERNET_DATA_KEY'),
    'ASKAI_TUI': ('enums.run_modes', 'ASKAI_TUI'),
    'AUDIO_SUFFIXES': ('capabilities.desktop', 'AUDIO_SUFFIXES'),
    'AUDIO_TAG': ('speech.audio_tags', 'AUDIO_TAG'),
    'AccColor': ('enums.acc_color', 'AccColor'),
    'AccResponse': ('model.acc_response', 'AccResponse'),
    'ActionResult': ('capabilities.desktop', 'ActionResult'),
    'AgentBackend': ('agents.contracts', 'AgentBackend'),
    'AgentError': ('agents.contracts', 'AgentError'),
    'AgentEvent': ('agents.contracts', 'AgentEvent'),
    'AgentResult': ('agents.contracts', 'AgentResult'),
    'AgentTask': ('agents.contracts', 'AgentTask'),
    'ApiKeys': ('model.api_keys', 'ApiKeys'),
    'AskAi': ('askai', 'AskAi'),
    'AskAiCli': ('askai_cli', 'AskAiCli'),
    'AskAiConfigs': ('askai_configs', 'AskAiConfigs'),
    'AskAiEvents': ('askai_events', 'AskAiEvents'),
    'AskAiMessages': ('askai_messages', 'AskAiMessages'),
    'AskAiPrompt': ('askai_prompt', 'AskAiPrompt'),
    'AskAiSettings': ('askai_settings', 'AskAiSettings'),
    'Assessment': ('component.answer_validator', 'Assessment'),
    'BAD': ('enums.acc_color', 'BAD'),
    'CAMERA_TOOL': ('agents.camera_tool', 'CAMERA_TOOL'),
    'CATEGORY_ICONS': ('component.internet_service', 'CATEGORY_ICONS'),
    'CATEGORY_ICONS': ('component.search_presentation', 'CATEGORY_ICONS'),
    'CHAT': ('enums.router_mode', 'CHAT'),
    'CHAT_ICONS': ('support.text_formatter', 'CHAT_ICONS'),
    'COMMANDER_HELP_TPL': ('commander.commander', 'COMMANDER_HELP_TPL'),
    'COMMAND_TOOL': ('agents.command_tool', 'COMMAND_TOOL'),
    'CacheService': ('component.cache_service', 'CacheService'),
    'ChatContext': ('support.chat_context', 'ChatContext'),
    'ChatProcessor': ('processors.chat', 'ChatProcessor'),
    'CodexBackend': ('agents.codex', 'CodexBackend'),
    'CodexConnections': ('agents.codex_connections', 'CodexConnections'),
    'CodexTTS': ('speech.codex_tts', 'CodexTTS'),
    'CommunicationBus': ('support.communication', 'CommunicationBus'),
    'Config': ('model.api_keys', 'Config'),
    'DEFERRED_COMMANDS': ('agents.command_tool', 'DEFERRED_COMMANDS'),
    'DENY': ('permissions.grants', 'DENY'),
    'DETAILED': ('enums.verbosity', 'DETAILED'),
    'DesktopCapabilities': ('capabilities.desktop', 'DesktopCapabilities'),
    'Document': ('component.retrieval', 'Document'),
    'DocumentModel': ('model.screenshot_result', 'DocumentModel'),
    'ELICITATION_METHOD': ('agents.elicitation', 'ELICITATION_METHOD'),
    'END_SILENCE_SECONDS': ('speech.dictation', 'END_SILENCE_SECONDS'),
    'ENGINES': ('engine.runtime', 'ENGINES'),
    'ENROLLMENT_TOOL': ('agents.enrollment_tool', 'ENROLLMENT_TOOL'),
    'EXCELLENT': ('enums.acc_color', 'EXCELLENT'),
    'ElevenLabsTTS': ('speech.elevenlabs_tts', 'ElevenLabsTTS'),
    'EngineFactory': ('engine.engine_factory', 'EngineFactory'),
    'EnrollmentFace': ('component.identity_enrollment', 'EnrollmentFace'),
    'EnrollmentPhoto': ('component.identity_enrollment', 'EnrollmentPhoto'),
    'FORM_MODES': ('agents.elicitation', 'FORM_MODES'),
    'FULL': ('enums.verbosity', 'FULL'),
    'FallbackTTS': ('speech.fallback_tts', 'FallbackTTS'),
    'GOOD': ('enums.acc_color', 'GOOD'),
    'GRANTS': ('permissions.grants', 'GRANTS'),
    'GeoLocation': ('component.geo_location', 'GeoLocation'),
    'GrantDenied': ('permissions.grants', 'GrantDenied'),
    'GrantPolicy': ('permissions.grants', 'GrantPolicy'),
    'GrantValue': ('permissions.grants', 'GrantValue'),
    'IDENTIFICATION_TOOL': ('agents.identification_tool', 'IDENTIFICATION_TOOL'),
    'INPUT_FORM_METHOD': ('agents.elicitation', 'INPUT_FORM_METHOD'),
    'INTERRUPT': ('enums.acc_color', 'INTERRUPT'),
    'IdentityEnrollment': ('component.identity_enrollment', 'IdentityEnrollment'),
    'ImageResult': ('model.image_result', 'ImageResult'),
    'Inference': ('engine.inference', 'Inference'),
    'InternetService': ('component.internet_service', 'InternetService'),
    'LOW': ('enums.verbosity', 'LOW'),
    'MAX_INPUT_CHARS': ('agents.input_context', 'MAX_INPUT_CHARS'),
    'MAX_OUTPUT': ('commander.command_results', 'MAX_OUTPUT'),
    'MAX_PENDING': ('speech.output_queue', 'MAX_PENDING'),
    'MAX_RESULTS': ('commander.command_results', 'MAX_RESULTS'),
    'MINIMUM': ('enums.verbosity', 'MINIMUM'),
    'MIN_SPEECH_WAIT_SECONDS': ('speech.capture', 'MIN_SPEECH_WAIT_SECONDS'),
    'MODERATE': ('enums.acc_color', 'MODERATE'),
    'MediaPlayer': ('capabilities.media_player', 'MediaPlayer'),
    'Message': ('support.short_term_memory', 'Message'),
    'NARRATION_PREFIX': ('speech.presentation', 'NARRATION_PREFIX'),
    'NEVER': ('permissions.grants', 'NEVER'),
    'NORMAL': ('enums.verbosity', 'NORMAL'),
    'Narration': ('speech.narration', 'Narration'),
    'NonInteractive': ('processors.qstring', 'NonInteractive'),
    'Orchestrator': ('orchestration.orchestrator', 'Orchestrator'),
    'PREFIX': ('permissions.grants', 'PREFIX'),
    'PROBE_TEXT': ('speech.codex_tts', 'PROBE_TEXT'),
    'PROBE_TEXT': ('speech.elevenlabs_tts', 'PROBE_TEXT'),
    'PROMPT_DIR': ('askai_prompt', 'PROMPT_DIR'),
    'PersistentMemory': ('support.persistent_memory', 'PersistentMemory'),
    'PlaybackEnded': ('capabilities.media_player', 'PlaybackEnded'),
    'PlaybackTiming': ('speech.timing', 'PlaybackTiming'),
    'QNA': ('enums.router_mode', 'QNA'),
    'QSTRING': ('enums.router_mode', 'QSTRING'),
    'QnA': ('processors.qna', 'QnA'),
    'RAG': ('enums.router_mode', 'RAG'),
    'RAGProvider': ('component.rag_provider', 'RAGProvider'),
    'REFINEMENT_SCHEMA': ('speech.dictation', 'REFINEMENT_SCHEMA'),
    'RESOURCE_DIR': ('askai_configs', 'RESOURCE_DIR'),
    'RE_MD_CODE_BLOCK': ('support.text_formatter', 'RE_MD_CODE_BLOCK'),
    'RE_MD_ESCAPES': ('support.text_formatter', 'RE_MD_ESCAPES'),
    'RE_TYPES': ('support.text_formatter', 'RE_TYPES'),
    'RE_URL': ('support.text_formatter', 'RE_URL'),
    'RICH_THEMES': ('support.text_formatter', 'RICH_THEMES'),
    'Rag': ('processors.rag', 'Rag'),
    'ReasoningSummaries': ('agents.reasoning_summaries', 'ReasoningSummaries'),
    'RecognizerSTT': ('speech.recognizer_stt', 'RecognizerSTT'),
    'RefinedResponse': ('model.refined_response', 'RefinedResponse'),
    'ReplyChannel': ('support.communication', 'ReplyChannel'),
    'RouterMode': ('enums.router_mode', 'RouterMode'),
    'RunModes': ('enums.run_modes', 'RunModes'),
    'RuntimeEngines': ('engine.runtime', 'RuntimeEngines'),
    'SAMPLE_RATE': ('speech.elevenlabs_tts', 'SAMPLE_RATE'),
    'SCREENSHOT_TOOL': ('agents.screenshot_tool', 'SCREENSHOT_TOOL'),
    'SESSION_MESSAGES': ('support.communication', 'SESSION_MESSAGES'),
    'SITE_ICONS': ('component.internet_service', 'SITE_ICONS'),
    'STTEngine': ('speech.contracts', 'STTEngine'),
    'Scheduler': ('component.scheduler', 'Scheduler'),
    'ScreenshotResult': ('model.screenshot_result', 'ScreenshotResult'),
    'SearchResult': ('model.search_result', 'SearchResult'),
    'SharedInstances': ('support.shared_instances', 'SharedInstances'),
    'ShortTermMemory': ('support.short_term_memory', 'ShortTermMemory'),
    'SpeechOutputQueue': ('speech.output_queue', 'SpeechOutputQueue'),
    'SpeechService': ('speech.service', 'SpeechService'),
    'StartedSpeechError': ('speech.pcm_stream', 'StartedSpeechError'),
    'StdioTransport': ('agents.stdio_transport', 'StdioTransport'),
    'Summarizer': ('component.summarizer', 'Summarizer'),
    'SummaryResult': ('model.summary_result', 'SummaryResult'),
    'T': ('support.llm_parser', 'T'),
    'TAIUS': ('enums.router_mode', 'TAIUS'),
    'TERMINATE': ('enums.acc_color', 'TERMINATE'),
    'TTSEngine': ('speech.contracts', 'TTSEngine'),
    'TaiusProcessor': ('processors.taius', 'TaiusProcessor'),
    'TextFormatter': ('support.text_formatter', 'TextFormatter'),
    'Usage': ('support.usage', 'Usage'),
    'VIDEO_SUFFIXES': ('capabilities.desktop', 'VIDEO_SUFFIXES'),
    'VOICE_INPUT_EVENT': ('askai_events', 'VOICE_INPUT_EVENT'),
    'VectorIndex': ('component.retrieval', 'VectorIndex'),
    'Verbosity': ('enums.verbosity', 'Verbosity'),
    'WHISPER_CONTROL_TOKEN': ('speech.recognizer_stt', 'WHISPER_CONTROL_TOKEN'),
    'WHISPER_LOGPROB_THRESHOLD': ('speech.recognizer_stt', 'WHISPER_LOGPROB_THRESHOLD'),
    'WebsiteModel': ('model.screenshot_result', 'WebsiteModel'),
    '_CommandOutput': ('commander.command_results', '_CommandOutput'),
    '_FinishableStream': ('speech.capture', '_FinishableStream'),
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
    'AIEngine',
    'AIModel',
    'AIProcessor',
    'AIReply',
    'AIVision',
    'ALLOW',
    'ASK',
    'ASKAI_BUS',
    'ASKAI_CLI',
    'ASKAI_CMD',
    'ASKAI_INTERNET_DATA_KEY',
    'ASKAI_TUI',
    'AUDIO_SUFFIXES',
    'AUDIO_TAG',
    'AccColor',
    'AccResponse',
    'ActionResult',
    'AgentBackend',
    'AgentError',
    'AgentEvent',
    'AgentResult',
    'AgentTask',
    'ApiKeys',
    'AskAi',
    'AskAiCli',
    'AskAiConfigs',
    'AskAiEvents',
    'AskAiMessages',
    'AskAiPrompt',
    'AskAiSettings',
    'Assessment',
    'BAD',
    'CAMERA_TOOL',
    'CATEGORY_ICONS',
    'CATEGORY_ICONS',
    'CHAT',
    'CHAT_ICONS',
    'COMMANDER_HELP_TPL',
    'COMMAND_TOOL',
    'CacheService',
    'ChatContext',
    'ChatProcessor',
    'CodexBackend',
    'CodexConnections',
    'CodexTTS',
    'CommunicationBus',
    'Config',
    'DEFERRED_COMMANDS',
    'DENY',
    'DETAILED',
    'DesktopCapabilities',
    'Document',
    'DocumentModel',
    'ELICITATION_METHOD',
    'END_SILENCE_SECONDS',
    'ENGINES',
    'ENROLLMENT_TOOL',
    'EXCELLENT',
    'ElevenLabsTTS',
    'EngineFactory',
    'EnrollmentFace',
    'EnrollmentPhoto',
    'FORM_MODES',
    'FULL',
    'FallbackTTS',
    'GOOD',
    'GRANTS',
    'GeoLocation',
    'GrantDenied',
    'GrantPolicy',
    'GrantValue',
    'IDENTIFICATION_TOOL',
    'INPUT_FORM_METHOD',
    'INTERRUPT',
    'IdentityEnrollment',
    'ImageResult',
    'Inference',
    'InternetService',
    'LOW',
    'MAX_INPUT_CHARS',
    'MAX_OUTPUT',
    'MAX_PENDING',
    'MAX_RESULTS',
    'MINIMUM',
    'MIN_SPEECH_WAIT_SECONDS',
    'MODERATE',
    'MediaPlayer',
    'Message',
    'NARRATION_PREFIX',
    'NEVER',
    'NORMAL',
    'Narration',
    'NonInteractive',
    'Orchestrator',
    'PREFIX',
    'PROBE_TEXT',
    'PROBE_TEXT',
    'PROMPT_DIR',
    'PersistentMemory',
    'PlaybackEnded',
    'PlaybackTiming',
    'QNA',
    'QSTRING',
    'QnA',
    'RAG',
    'RAGProvider',
    'REFINEMENT_SCHEMA',
    'RESOURCE_DIR',
    'RE_MD_CODE_BLOCK',
    'RE_MD_ESCAPES',
    'RE_TYPES',
    'RE_URL',
    'RICH_THEMES',
    'Rag',
    'ReasoningSummaries',
    'RecognizerSTT',
    'RefinedResponse',
    'ReplyChannel',
    'RouterMode',
    'RunModes',
    'RuntimeEngines',
    'SAMPLE_RATE',
    'SCREENSHOT_TOOL',
    'SESSION_MESSAGES',
    'SITE_ICONS',
    'STTEngine',
    'Scheduler',
    'ScreenshotResult',
    'SearchResult',
    'SharedInstances',
    'ShortTermMemory',
    'SpeechOutputQueue',
    'SpeechService',
    'StartedSpeechError',
    'StdioTransport',
    'Summarizer',
    'SummaryResult',
    'T',
    'TAIUS',
    'TERMINATE',
    'TTSEngine',
    'TaiusProcessor',
    'TextFormatter',
    'Usage',
    'VIDEO_SUFFIXES',
    'VOICE_INPUT_EVENT',
    'VectorIndex',
    'Verbosity',
    'WHISPER_CONTROL_TOKEN',
    'WHISPER_LOGPROB_THRESHOLD',
    'WebsiteModel',
    '_CommandOutput',
    '_FinishableStream',
    'agents',
    'askai',
    'askai_cli',
    'askai_configs',
    'askai_events',
    'askai_messages',
    'askai_prompt',
    'askai_settings',
    'capabilities',
    'commander',
    'component',
    'engine',
    'enums',
    'model',
    'orchestration',
    'permissions',
    'processors',
    'router',
    'speech',
    'support'
]
__version__ = '2.0.1'
