# _*_ coding: utf-8 _*_
#
# $app_name v2.0.1
#
# Package: main.askai.gestures
"""Package initialization."""

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .scroll import BOTTOM_LIMIT
    from .controller import CAMERA_MARGIN
    from .controller import CLOSE_RATIO
    from .controller import DEAD_ZONE
    from .controller import DRAG_HOLD_SECONDS
    from .controller import EXIT_HOLD_SECONDS
    from .pointer_response import FAST_SPEED
    from .controller import FINE_POINTER_DISTANCE
    from .controller import FINE_POINTER_MIN_FACTOR
    from .thumbs_up import FOLDED_FINGERS
    from .thumbs_up import FOLDED_RATIO
    from .session import GRANTS
    from .controller import GestureController
    from .controller import GestureState
    from .tracker import HandTracker
    from .session import INACTIVITY_SECONDS
    from .preview import INITIAL_SIZE
    from .preview import LABELS
    from .pointer_response import MAX_FACTOR
    from .pointer_response import MAX_GAP_SECONDS
    from .thumbs_up import MAX_HORIZONTAL_RATIO
    from .scroll import MAX_STEPS
    from .command import MESSAGES
    from .pointer_response import MIN_FACTOR
    from .pointer_response import MIN_SAMPLE_SECONDS
    from .thumbs_up import MIN_THUMB_HEIGHT_RATIO
    from .tracker import MODEL_URL
    from .scroll import NEUTRAL_BOTTOM
    from .scroll import NEUTRAL_TOP
    from .controller import OPEN_RATIO
    from .preview import Pointer
    from .pointer_response import PointerResponse
    from .preview import Preview
    from .pointer_response import RESPONSE_SECONDS
    from .controller import SCROLL_COOLDOWN_SECONDS
    from .controller import SCROLL_IDLE_SECONDS
    from .scroll import SCROLL_INTERVAL
    from .sfx import SFX_DIR
    from .controller import SMOOTHING
    from .thumbs_up import STRAIGHT_COSINE
    from .scroll import ScrollMotion
    from .preview import TITLE
    from .scroll import TOP_LIMIT


_EXPORTS = {
    'BOTTOM_LIMIT': ('scroll', 'BOTTOM_LIMIT'),
    'CAMERA_MARGIN': ('controller', 'CAMERA_MARGIN'),
    'CLOSE_RATIO': ('controller', 'CLOSE_RATIO'),
    'DEAD_ZONE': ('controller', 'DEAD_ZONE'),
    'DRAG_HOLD_SECONDS': ('controller', 'DRAG_HOLD_SECONDS'),
    'EXIT_HOLD_SECONDS': ('controller', 'EXIT_HOLD_SECONDS'),
    'FAST_SPEED': ('pointer_response', 'FAST_SPEED'),
    'FINE_POINTER_DISTANCE': ('controller', 'FINE_POINTER_DISTANCE'),
    'FINE_POINTER_MIN_FACTOR': ('controller', 'FINE_POINTER_MIN_FACTOR'),
    'FOLDED_FINGERS': ('thumbs_up', 'FOLDED_FINGERS'),
    'FOLDED_RATIO': ('thumbs_up', 'FOLDED_RATIO'),
    'GRANTS': ('session', 'GRANTS'),
    'GestureController': ('controller', 'GestureController'),
    'GestureState': ('controller', 'GestureState'),
    'HandTracker': ('tracker', 'HandTracker'),
    'INACTIVITY_SECONDS': ('session', 'INACTIVITY_SECONDS'),
    'INITIAL_SIZE': ('preview', 'INITIAL_SIZE'),
    'LABELS': ('preview', 'LABELS'),
    'MAX_FACTOR': ('pointer_response', 'MAX_FACTOR'),
    'MAX_GAP_SECONDS': ('pointer_response', 'MAX_GAP_SECONDS'),
    'MAX_HORIZONTAL_RATIO': ('thumbs_up', 'MAX_HORIZONTAL_RATIO'),
    'MAX_STEPS': ('scroll', 'MAX_STEPS'),
    'MESSAGES': ('command', 'MESSAGES'),
    'MIN_FACTOR': ('pointer_response', 'MIN_FACTOR'),
    'MIN_SAMPLE_SECONDS': ('pointer_response', 'MIN_SAMPLE_SECONDS'),
    'MIN_THUMB_HEIGHT_RATIO': ('thumbs_up', 'MIN_THUMB_HEIGHT_RATIO'),
    'MODEL_URL': ('tracker', 'MODEL_URL'),
    'NEUTRAL_BOTTOM': ('scroll', 'NEUTRAL_BOTTOM'),
    'NEUTRAL_TOP': ('scroll', 'NEUTRAL_TOP'),
    'OPEN_RATIO': ('controller', 'OPEN_RATIO'),
    'Pointer': ('preview', 'Pointer'),
    'PointerResponse': ('pointer_response', 'PointerResponse'),
    'Preview': ('preview', 'Preview'),
    'RESPONSE_SECONDS': ('pointer_response', 'RESPONSE_SECONDS'),
    'SCROLL_COOLDOWN_SECONDS': ('controller', 'SCROLL_COOLDOWN_SECONDS'),
    'SCROLL_IDLE_SECONDS': ('controller', 'SCROLL_IDLE_SECONDS'),
    'SCROLL_INTERVAL': ('scroll', 'SCROLL_INTERVAL'),
    'SFX_DIR': ('sfx', 'SFX_DIR'),
    'SMOOTHING': ('controller', 'SMOOTHING'),
    'STRAIGHT_COSINE': ('thumbs_up', 'STRAIGHT_COSINE'),
    'ScrollMotion': ('scroll', 'ScrollMotion'),
    'TITLE': ('preview', 'TITLE'),
    'TOP_LIMIT': ('scroll', 'TOP_LIMIT')
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
    'BOTTOM_LIMIT',
    'CAMERA_MARGIN',
    'CLOSE_RATIO',
    'DEAD_ZONE',
    'DRAG_HOLD_SECONDS',
    'EXIT_HOLD_SECONDS',
    'FAST_SPEED',
    'FINE_POINTER_DISTANCE',
    'FINE_POINTER_MIN_FACTOR',
    'FOLDED_FINGERS',
    'FOLDED_RATIO',
    'GRANTS',
    'GestureController',
    'GestureState',
    'HandTracker',
    'INACTIVITY_SECONDS',
    'INITIAL_SIZE',
    'LABELS',
    'MAX_FACTOR',
    'MAX_GAP_SECONDS',
    'MAX_HORIZONTAL_RATIO',
    'MAX_STEPS',
    'MESSAGES',
    'MIN_FACTOR',
    'MIN_SAMPLE_SECONDS',
    'MIN_THUMB_HEIGHT_RATIO',
    'MODEL_URL',
    'NEUTRAL_BOTTOM',
    'NEUTRAL_TOP',
    'OPEN_RATIO',
    'Pointer',
    'PointerResponse',
    'Preview',
    'RESPONSE_SECONDS',
    'SCROLL_COOLDOWN_SECONDS',
    'SCROLL_IDLE_SECONDS',
    'SCROLL_INTERVAL',
    'SFX_DIR',
    'SMOOTHING',
    'STRAIGHT_COSINE',
    'ScrollMotion',
    'TITLE',
    'TOP_LIMIT',
    'background',
    'command',
    'controller',
    'palm',
    'phone',
    'pointer_response',
    'preview',
    'rock',
    'scroll',
    'session',
    'sfx',
    'thumbs_up',
    'tracker',
    'worker'
]
__version__ = '2.0.1'
