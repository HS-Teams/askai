# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: demo.devel
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .spinner import ARROW_BAR
    from .eleven_labs_recon import AUDIO_OUTPUT_PATH
    from .spinner import BAR
    from .spinner import BOUNCE
    from .spinner import BOX
    from .spinner import BULLET
    from .animated_ascii import CELL_ASPECT
    from .spinner import CIRCLE
    from .spinner import COLIMA
    from .spinner import DEFAULT
    from .animated_ascii import DEFAULT_PALETTE
    from .eleven_labs_recon import ELEVENLABS_API_KEY
    from .eleven_labs import ELEVENLABS_API_KEY
    from .transcribe import FILE
    from .animated_ascii import FPS
    from .gesture_action_manager import GestureActionManager
    from .spinner import HEXAGON
    from .spinner import LINE_BOUNCE
    from .spinner import LINE_GROW
    from .whisper_tests import MODEL_MAP
    from .gesture_action_manager import NUM_FRAMES
    from .gesture_action_manager import NUM_KEYPOINTS
    from .gesture_action_manager import NUM_VIDEOS
    from .animated_ascii import PALETTES
    from .spinner import STAR
    from .spinner import Spinner
    from .animated_ascii import VIDEO_DIR
    from .eleven_labs_recon import VOICE_ID


_EXPORTS = {
    'ARROW_BAR': ('spinner', 'ARROW_BAR'),
    'AUDIO_OUTPUT_PATH': ('eleven_labs_recon', 'AUDIO_OUTPUT_PATH'),
    'BAR': ('spinner', 'BAR'),
    'BOUNCE': ('spinner', 'BOUNCE'),
    'BOX': ('spinner', 'BOX'),
    'BULLET': ('spinner', 'BULLET'),
    'CELL_ASPECT': ('animated_ascii', 'CELL_ASPECT'),
    'CIRCLE': ('spinner', 'CIRCLE'),
    'COLIMA': ('spinner', 'COLIMA'),
    'DEFAULT': ('spinner', 'DEFAULT'),
    'DEFAULT_PALETTE': ('animated_ascii', 'DEFAULT_PALETTE'),
    'ELEVENLABS_API_KEY': ('eleven_labs_recon', 'ELEVENLABS_API_KEY'),
    'ELEVENLABS_API_KEY': ('eleven_labs', 'ELEVENLABS_API_KEY'),
    'FILE': ('transcribe', 'FILE'),
    'FPS': ('animated_ascii', 'FPS'),
    'GestureActionManager': ('gesture_action_manager', 'GestureActionManager'),
    'HEXAGON': ('spinner', 'HEXAGON'),
    'LINE_BOUNCE': ('spinner', 'LINE_BOUNCE'),
    'LINE_GROW': ('spinner', 'LINE_GROW'),
    'MODEL_MAP': ('whisper_tests', 'MODEL_MAP'),
    'NUM_FRAMES': ('gesture_action_manager', 'NUM_FRAMES'),
    'NUM_KEYPOINTS': ('gesture_action_manager', 'NUM_KEYPOINTS'),
    'NUM_VIDEOS': ('gesture_action_manager', 'NUM_VIDEOS'),
    'PALETTES': ('animated_ascii', 'PALETTES'),
    'STAR': ('spinner', 'STAR'),
    'Spinner': ('spinner', 'Spinner'),
    'VIDEO_DIR': ('animated_ascii', 'VIDEO_DIR'),
    'VOICE_ID': ('eleven_labs_recon', 'VOICE_ID')
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
    'ARROW_BAR',
    'AUDIO_OUTPUT_PATH',
    'BAR',
    'BOUNCE',
    'BOX',
    'BULLET',
    'CELL_ASPECT',
    'CIRCLE',
    'COLIMA',
    'DEFAULT',
    'DEFAULT_PALETTE',
    'ELEVENLABS_API_KEY',
    'ELEVENLABS_API_KEY',
    'FILE',
    'FPS',
    'GestureActionManager',
    'HEXAGON',
    'LINE_BOUNCE',
    'LINE_GROW',
    'MODEL_MAP',
    'NUM_FRAMES',
    'NUM_KEYPOINTS',
    'NUM_VIDEOS',
    'PALETTES',
    'STAR',
    'Spinner',
    'VIDEO_DIR',
    'VOICE_ID',
    'animated_ascii',
    'eleven_labs',
    'eleven_labs_recon',
    'gesture_action_manager',
    'google_suggestions',
    'gpt2_suggester',
    'gpt_zip',
    'rich-test',
    'saridom',
    'serpapi_test',
    'spinner',
    'transcribe',
    'vision-tests',
    'whisper_tests'
]
__version__ = '2.0.1'
