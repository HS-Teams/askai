#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.component
   @file: audio_player.py
@created: Wed, 22 Feb 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from askai.__classpath__ import classpath
from clitt.core.term.terminal import Terminal
from functools import lru_cache
from hspylib.core.metaclass.singleton import Singleton
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith
from hspylib.modules.application.exit_status import ExitStatus
from pathlib import Path
from shutil import which
from typing import Literal

import logging as log
import time


class AudioPlayer(metaclass=Singleton):
    """Provide an interface for playing audio through the default speaker device. This class allows for the playback of
    audio files using the system's default audio output device.
    """

    INSTANCE: "AudioPlayer"

    # Sound effects directory.
    SFX_DIR = str(classpath.resource_path) + "/sfx"

    @staticmethod
    def play_audio_file(path_to_audio_file: str | Path, tempo: int = 1, loop: float | None = None) -> bool:
        """Play the specified audio file using the ffplay (ffmpeg) application.
        :param path_to_audio_file: The path to the audio file (e.g., MP3) to be played.
        :param tempo: The playback speed (default is 1).
        :param loop: Whether to loop the audio playback (None for no looping).
        :return: True if the audio file is played successfully, otherwise False.
        """
        if file_is_not_empty(str(path_to_audio_file)):
            try:
                loop_args = f"-loop {loop} " if loop else ""
                _, _, code = Terminal.shell_exec(
                    f'ffplay -af "atempo={tempo}" -v 0 -nodisp -autoexit {loop_args}{path_to_audio_file}'
                )
                return code == ExitStatus.SUCCESS
            except FileNotFoundError:
                log.error("Audio file was not found: %s !", path_to_audio_file)

        return False

    @staticmethod
    def play_sfx(filename: str, file_ext: Literal[".mp3", ".wav", ".m4a"] = ".mp3", loop: float | None = None) -> bool:
        """Play a sound effect audio file.
        :param filename: The name of the sound effect file (without the extension).
        :param file_ext: The file extension of the sound effect (default is ".mp3").
        :param loop: Whether to loop the audio playback (None for no looping).
        :return: True if the sound effect is played successfully, otherwise False.
        """
        filename = f"{AudioPlayer.SFX_DIR}/{ensure_endswith(filename, file_ext)}"
        check_argument(file_is_not_empty(filename), f"Sound effects file does not exist: {filename}")

        from askai.core.speech.effects import play
        return play(filename, loop=loop)

    def __init__(self):
        check_argument(which("ffplay") is not None, "ffmpeg::ffplay is required to play audio")

    @lru_cache
    def start_delay(self) -> float:
        """Determine the amount of delay before start streaming the text."""
        log.debug("Determining the start delay")
        sample_duration_sec = 1.75  # We know the length
        started = time.time()
        self.play_sfx("ui/sample.mp3")
        delay = max(0.0, time.time() - started - sample_duration_sec)
        log.debug("Detected a play delay of %s seconds", delay)

        return delay

    @lru_cache
    def audio_length(self, path_to_audio_file: str) -> float:
        """Determine the length of an audio file using ffmpeg.
        :param path_to_audio_file: The path to the audio file whose length is to be determined.
        :return: The length of the audio file in seconds as a float.
        """
        check_argument(which("ffprobe") and file_is_not_empty(path_to_audio_file))
        out: float = 0.0
        try:
            out, _, code = Terminal.shell_exec(
                f'ffprobe -i {path_to_audio_file} -show_entries format=duration -v quiet -of csv="p=0"'
            )
            return float(out) if code == ExitStatus.SUCCESS else 0.0
        except FileNotFoundError:
            log.error("Audio file was not found: %s !", path_to_audio_file)
        except TypeError:
            log.error("Could not determine audio duration !")

        return out


assert (player := AudioPlayer().INSTANCE) is not None
