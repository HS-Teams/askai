"""Play gesture feedback without blocking camera processing."""
import logging
from pathlib import Path
import subprocess
from threading import Thread

SFX_DIR = Path(__file__).resolve().parents[1] / 'resources/sfx'


def play_click():
    _play('gesture-click.ogg')


def play_drag():
    _play('gesture-move.mp3')


def play_escape():
    _play('gesture-stop.mp3')


def play_quit():
    _play('gesture-quit.mp3')


def play_ptt():
    _play('gesture-ptt.mp3')


def play_init():
    _play('gesture-init.mp3')


def _play(filename):
    def play():
        try:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'error', str(SFX_DIR / filename)],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=True, timeout=5)
        except (OSError, subprocess.SubprocessError):
            logging.exception('Cannot play gesture sound: %s', filename)
    Thread(target=play, daemon=True).start()
