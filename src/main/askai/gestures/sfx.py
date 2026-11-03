"""Play gesture feedback without blocking camera processing."""
import logging
from pathlib import Path
import subprocess
from threading import Thread

SFX_DIR = Path(__file__).resolve().parents[1] / 'resources/sfx/gestures'


def play_click():
    _play('gesture-click.ogg')


def play_double_click():
    _play('gesture-double-click.mp3')


def play_grab():
    _play('gesture-grab.mp3')


def play_drag():
    _play('gesture-move.mp3')


def play_scroll_up():
    _play('gesture-slide-up.mp3')


def play_scroll_down():
    _play('gesture-slide-down.mp3')


def play_abort():
    _play('gesture-stop.mp3')


def play_quit():
    _play('gesture-quit.mp3')


def play_ptt():
    _play('gesture-ptt.mp3')


def play_init():
    _play('gesture-init.mp3')


def _play(filename):
    from askai.core.speech import effects
    if effects.is_muted():
        return
    def play():
        try:
            if not effects.play(SFX_DIR / filename, timeout=5):
                logging.error('Cannot play gesture sound: %s', filename)
        except (OSError, subprocess.SubprocessError):
            logging.exception('Cannot play gesture sound: %s', filename)
    Thread(target=play, daemon=True).start()
