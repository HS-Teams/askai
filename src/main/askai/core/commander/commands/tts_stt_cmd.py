#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@project: HsPyLib-AskAI
@package: askai.core.commander.tts_stt_cmd
   @file: tts_stt_cmd.py
@created: Thu, 25 Apr 2024
 @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
   @site: https://github.com/yorevs/askai
@license: MIT - Please refer to <https://opensource.org/licenses/MIT>

Copyright (c) 2024, AskAI
"""
from abc import ABC
from pathlib import Path
from textwrap import dedent
import os

from clitt.core.tui.mselect.mselect import mselect
import pause

from askai.core.askai_configs import configs
from askai.core.askai_settings import settings
from askai.core.component.multimedia.recorder import InputDevice, recorder
from askai.core.support.shared_instances import shared
from askai.core.support.text_formatter import text_formatter
from askai.core.support.utilities import copy_file


class TtsSttCmd(ABC):
    """Provides Speech-to-Text (STT) and Text-to-Speech (TTS) command functionalities."""

    @staticmethod
    def voice_list() -> None:
        speech = shared.speech.tts
        voices = "\n".join(f"{i}. {voice}" for i, voice in enumerate(speech.voices()))
        text_formatter.commander_print(
            f"Available `{speech.model_name}` voices:\n{voices}\n"
            f"Current voice: `{speech.voice}`\n"
            '> Use `/voices set "voice name"` or `/voices play <number|voice_name>`.'
        )

    @staticmethod
    def voice_set(name_or_index: str | int | None = None) -> None:
        speech = shared.speech.tts
        if voice := TtsSttCmd._resolve_voice(name_or_index):
            speech.select_voice(voice)
            text_formatter.commander_print(f"Voice changed to `{voice}`")

    @staticmethod
    def voice_play(name_or_index: str | int | None = None) -> None:
        if voice := TtsSttCmd._resolve_voice(name_or_index):
            shared.speech.tts.synthesize(
                "Hello! This is a sample of my voice.", stream=False, voice=voice
            )

    @staticmethod
    def _resolve_voice(name_or_index: str | int | None) -> str | None:
        speech = shared.speech.tts
        voices = speech.voices()
        value = str(name_or_index) if name_or_index is not None else speech.voice
        if value.isdecimal():
            index = int(value)
            if 0 <= index < len(voices):
                return voices[index]
        else:
            for voice in voices:
                if voice.casefold() == value.casefold():
                    return voice
        text_formatter.commander_print(f"%RED%Invalid voice name/index: '{value}'%NC%")
        return None

    @staticmethod
    def tempo(speed: int | None = None) -> None:
        """Set the playing speed of the speech.
        :param speed: The speed to set for speech playback. If None, the default speed will be used.
        """
        if not speed:
            settings.get("askai.text.to.speech.tempo")
        elif 1 <= speed <= 3:
            settings.put("askai.text.to.speech.tempo", speed)
            configs.tempo = speed
            tempo_str: str = "Normal" if speed == 1 else ("Fast" if speed == 2 else "Ultra")
            text_formatter.commander_print(f"`Speech-To-Text` **tempo** changed to %GREEN%{tempo_str} ({speed})%NC%")
        else:
            text_formatter.commander_print(f"%RED%Invalid tempo value: '{speed}'. Please choose between [1..3].%NC%")

    @staticmethod
    def device_list() -> None:
        """List the available audio input devices."""
        all_devices = recorder.devices
        str_devices = "\n".join([f"{d[0]}. {d[1]}" for d in all_devices])
        text_formatter.commander_print(
            f"Current audio input device: {recorder.input_device} \n"
            f"\nAvailable audio input devices: \n"
            f"\n{str_devices}\n> Hint: Type: '/devices set \\<number\\>' to select a device."
        )

    @staticmethod
    def device_set(name_or_index: str | int | None = None) -> None:
        """Set the current audio input device.
        :param name_or_index: The name or index of the audio input device to set. If None, the default device will be
                              used.
        """
        device: InputDevice | None = None
        all_devices = recorder.devices

        def _set_device(_device) -> bool:
            if recorder.set_device(_device):
                text_formatter.commander_print(f"`Text-To-Speech` device changed to %GREEN%{_device}%NC%")
                return True
            text_formatter.commander_print(f"%HOM%%ED2%Error: '{_device}' is not an Audio Input device!%NC%")
            all_devices.remove(_device)
            pause.seconds(2)
            return False

        if not name_or_index:
            device = mselect(all_devices, f"{'-=' * 40}%EOL%AskAI::Select the Audio Input device%EOL%{'=-' * 40}%EOL%")
        elif name_or_index.isdecimal() and 0 <= int(name_or_index) <= len(all_devices):
            name_or_index = all_devices[int(name_or_index)][1]
            device = next((dev for dev in all_devices if dev[1] == name_or_index), None)
        if not (device and _set_device(device)):
            text_formatter.commander_print(f"%RED%Invalid audio input device: '{name_or_index}'%NC%")

    @staticmethod
    def tts(text: str, dest_dir: str = os.getcwd(), playback: bool = True) -> None:
        """Convert text to speech and optionally play it back.
        :param text: The text to be converted to speech.
        :param dest_dir: The directory where the audio file will be saved (default is the current working directory).
        :param playback: Whether to play back the generated speech after conversion (default is True).
        """
        if (audio_path := shared.speech.tts.synthesize(text, stream=False, playback=playback)) and audio_path.exists():
            if dest_dir and ((dest_path := Path(dest_dir)) and dest_path.exists()):
                audio_path = copy_file(audio_path, dest_dir)
            text_formatter.commander_print(f"File %GREEN%'{audio_path}' was successfully saved!%NC%")
        else:
            text_formatter.commander_print(f"%RED%Unable to convert text to file !%NC%")

    @staticmethod
    def dictate(dest_file: str | None) -> None:
        """Dictates text and optionally saves it to a file.
        :param dest_file: The destination file path where the dictated text will be saved, or None if no file is specified.
        """
        file_info: str = f"Dictated text saved: *'{dest_file}'*" if dest_file else ""
        dictated_text: str | None = recorder.dictate()

        if dictated_text:
            if dest_file and os.path.exists(os.path.dirname(dest_file)):
                with open(dest_file, "w") as f_dictation:
                    f_dictation.write(dictated_text + os.linesep)
            # fmt: off
            text_formatter.commander_print(
                dedent(f"""\
                {file_info}
                Dictated text: ` {dictated_text} `
                """).strip())
            # fmt: on
        else:
            text_formatter.commander_print(f"Dictation *produced no text* !")
