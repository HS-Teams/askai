# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.core.speech
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .audio_tags import AUDIO_TAG
    from .codex_tts import CodexTTS
    from .dictation import END_SILENCE_SECONDS
    from .elevenlabs_tts import ElevenLabsTTS
    from .fallback_tts import FallbackTTS
    from .output_queue import MAX_PENDING
    from .capture import MIN_SPEECH_WAIT_SECONDS
    from .presentation import NARRATION_PREFIX
    from .narration import Narration
    from .codex_tts import PROBE_TEXT
    from .elevenlabs_tts import PROBE_TEXT
    from .timing import PlaybackTiming
    from .dictation import REFINEMENT_SCHEMA
    from .recognizer_stt import RecognizerSTT
    from .elevenlabs_tts import SAMPLE_RATE
    from .contracts import STTEngine
    from .output_queue import SpeechOutputQueue
    from .service import SpeechService
    from .pcm_stream import StartedSpeechError
    from .contracts import TTSEngine
    from .recognizer_stt import WHISPER_CONTROL_TOKEN
    from .recognizer_stt import WHISPER_LOGPROB_THRESHOLD
    from .capture import _FinishableStream


_EXPORTS = {
    'AUDIO_TAG': ('audio_tags', 'AUDIO_TAG'),
    'CodexTTS': ('codex_tts', 'CodexTTS'),
    'END_SILENCE_SECONDS': ('dictation', 'END_SILENCE_SECONDS'),
    'ElevenLabsTTS': ('elevenlabs_tts', 'ElevenLabsTTS'),
    'FallbackTTS': ('fallback_tts', 'FallbackTTS'),
    'MAX_PENDING': ('output_queue', 'MAX_PENDING'),
    'MIN_SPEECH_WAIT_SECONDS': ('capture', 'MIN_SPEECH_WAIT_SECONDS'),
    'NARRATION_PREFIX': ('presentation', 'NARRATION_PREFIX'),
    'Narration': ('narration', 'Narration'),
    'PROBE_TEXT': ('codex_tts', 'PROBE_TEXT'),
    'PROBE_TEXT': ('elevenlabs_tts', 'PROBE_TEXT'),
    'PlaybackTiming': ('timing', 'PlaybackTiming'),
    'REFINEMENT_SCHEMA': ('dictation', 'REFINEMENT_SCHEMA'),
    'RecognizerSTT': ('recognizer_stt', 'RecognizerSTT'),
    'SAMPLE_RATE': ('elevenlabs_tts', 'SAMPLE_RATE'),
    'STTEngine': ('contracts', 'STTEngine'),
    'SpeechOutputQueue': ('output_queue', 'SpeechOutputQueue'),
    'SpeechService': ('service', 'SpeechService'),
    'StartedSpeechError': ('pcm_stream', 'StartedSpeechError'),
    'TTSEngine': ('contracts', 'TTSEngine'),
    'WHISPER_CONTROL_TOKEN': ('recognizer_stt', 'WHISPER_CONTROL_TOKEN'),
    'WHISPER_LOGPROB_THRESHOLD': ('recognizer_stt', 'WHISPER_LOGPROB_THRESHOLD'),
    '_FinishableStream': ('capture', '_FinishableStream')
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
    'AUDIO_TAG',
    'CodexTTS',
    'END_SILENCE_SECONDS',
    'ElevenLabsTTS',
    'FallbackTTS',
    'MAX_PENDING',
    'MIN_SPEECH_WAIT_SECONDS',
    'NARRATION_PREFIX',
    'Narration',
    'PROBE_TEXT',
    'PROBE_TEXT',
    'PlaybackTiming',
    'REFINEMENT_SCHEMA',
    'RecognizerSTT',
    'SAMPLE_RATE',
    'STTEngine',
    'SpeechOutputQueue',
    'SpeechService',
    'StartedSpeechError',
    'TTSEngine',
    'WHISPER_CONTROL_TOKEN',
    'WHISPER_LOGPROB_THRESHOLD',
    '_FinishableStream',
    'audio_tags',
    'capture',
    'codex_tts',
    'contracts',
    'dictation',
    'dictation_memory',
    'elevenlabs_tts',
    'factory',
    'fallback_tts',
    'listening_timer',
    'narration',
    'output_queue',
    'pcm_stream',
    'playback',
    'presentation',
    'recognizer_stt',
    'service',
    'timing'
]
__version__ = '2.0.1'
