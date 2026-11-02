# _*_ coding: utf-8 _*_
#
# $app_name v2.0.0
#
# Package: demo
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .devel.spinner import ARROW_BAR
    from .devel.eleven_labs_recon import AUDIO_OUTPUT_PATH
    from .devel.spinner import BAR
    from .devel.spinner import BOUNCE
    from .devel.spinner import BOX
    from .devel.spinner import BULLET
    from .devel.animated_ascii import CELL_ASPECT
    from .devel.spinner import CIRCLE
    from .devel.spinner import COLIMA
    from .devel.spinner import DEFAULT
    from .devel.animated_ascii import DEFAULT_PALETTE
    from .devel.eleven_labs_recon import ELEVENLABS_API_KEY
    from .devel.eleven_labs import ELEVENLABS_API_KEY
    from .devel.transcribe import FILE
    from .devel.animated_ascii import FPS
    from .devel.gesture_action_manager import GestureActionManager
    from .devel.spinner import HEXAGON
    from .devel.spinner import LINE_BOUNCE
    from .devel.spinner import LINE_GROW
    from .devel.whisper_tests import MODEL_MAP
    from .devel.gesture_action_manager import NUM_FRAMES
    from .devel.gesture_action_manager import NUM_KEYPOINTS
    from .devel.gesture_action_manager import NUM_VIDEOS
    from .devel.animated_ascii import PALETTES
    from .devel.spinner import STAR
    from .devel.spinner import Spinner
    from .devel.animated_ascii import VIDEO_DIR
    from .devel.eleven_labs_recon import VOICE_ID


_EXPORTS = {
    'ARROW_BAR': ('devel.spinner', 'ARROW_BAR'),
    'AUDIO_OUTPUT_PATH': ('devel.eleven_labs_recon', 'AUDIO_OUTPUT_PATH'),
    'BAR': ('devel.spinner', 'BAR'),
    'BOUNCE': ('devel.spinner', 'BOUNCE'),
    'BOX': ('devel.spinner', 'BOX'),
    'BULLET': ('devel.spinner', 'BULLET'),
    'CELL_ASPECT': ('devel.animated_ascii', 'CELL_ASPECT'),
    'CIRCLE': ('devel.spinner', 'CIRCLE'),
    'COLIMA': ('devel.spinner', 'COLIMA'),
    'DEFAULT': ('devel.spinner', 'DEFAULT'),
    'DEFAULT_PALETTE': ('devel.animated_ascii', 'DEFAULT_PALETTE'),
    'ELEVENLABS_API_KEY': ('devel.eleven_labs_recon', 'ELEVENLABS_API_KEY'),
    'ELEVENLABS_API_KEY': ('devel.eleven_labs', 'ELEVENLABS_API_KEY'),
    'FILE': ('devel.transcribe', 'FILE'),
    'FPS': ('devel.animated_ascii', 'FPS'),
    'GestureActionManager': ('devel.gesture_action_manager', 'GestureActionManager'),
    'HEXAGON': ('devel.spinner', 'HEXAGON'),
    'LINE_BOUNCE': ('devel.spinner', 'LINE_BOUNCE'),
    'LINE_GROW': ('devel.spinner', 'LINE_GROW'),
    'MODEL_MAP': ('devel.whisper_tests', 'MODEL_MAP'),
    'NUM_FRAMES': ('devel.gesture_action_manager', 'NUM_FRAMES'),
    'NUM_KEYPOINTS': ('devel.gesture_action_manager', 'NUM_KEYPOINTS'),
    'NUM_VIDEOS': ('devel.gesture_action_manager', 'NUM_VIDEOS'),
    'PALETTES': ('devel.animated_ascii', 'PALETTES'),
    'STAR': ('devel.spinner', 'STAR'),
    'Spinner': ('devel.spinner', 'Spinner'),
    'VIDEO_DIR': ('devel.animated_ascii', 'VIDEO_DIR'),
    'VOICE_ID': ('devel.eleven_labs_recon', 'VOICE_ID')
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
    'devel',
    'openai-api-full-demo',
    'others'
]
__version__ = '2.0.0'
