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
    def voice_list() -> dict:
        active = shared.speech.tts
        speech = getattr(active, "voice_engine", active)
        refresh = getattr(speech, "refresh_voices", speech.voices)
        catalogue = [{'index': index, 'name': voice} for index, voice in enumerate(refresh())]
        voices = "\n".join(f"{voice['index']}. {voice['name']}" for voice in catalogue)
        text_formatter.commander_print(
            f"Available `{speech.model_name}` voices:\n{voices}\n"
            f"Current voice: `{speech.voice}`\n"
            '> Use `/voices set "voice name"` or `/voices play <number|voice_name>`.'
        )
        return {'voices': catalogue, 'index_base': 0, 'model': speech.model_name, 'selected_voice': speech.voice}

    @staticmethod
    def voice_set(name_or_index: str | int | None = None) -> dict:
        speech = shared.speech.tts
        if voice := TtsSttCmd._resolve_voice(name_or_index):
            speech.select_voice(voice)
            text_formatter.commander_print(f"Voice changed to `{voice}`")
            return {'selected_voice': speech.voice, 'requested_voice': voice}
        return {'status': 'failed', 'error': f'Invalid voice name/index: {name_or_index}'}

    @staticmethod
    def voice_play(name_or_index: str | int | None = None) -> dict:
        if voice := TtsSttCmd._resolve_voice(name_or_index):
            active = shared.speech.tts
            speech = getattr(active, "voice_engine", active)
            speech.synthesize(
                "Hello! This is a sample of my voice.", stream=False, voice=voice
            )
            return {'preview_voice': voice}
        return {'status': 'failed', 'error': f'Invalid voice name/index: {name_or_index}'}

    @staticmethod
    def _resolve_voice(name_or_index: str | int | None) -> str | None:
        active = shared.speech.tts
        speech = getattr(active, "voice_engine", active)
        voices = speech.voices()
        value = str(name_or_index) if name_or_index is not None else speech.voice
        if value and value == speech.voice:
            return value
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
        from uuid import uuid4
        import pyperclip

        from askai.core.askai_messages import msg
        from askai.core.askai_prompt import prompt
        from askai.core.speech import dictation
        from askai.cli.dictation_input import finish_requested
        from askai.core.support.app_paths import askai_data_dir
        from askai.core.support.inference import complete
        from askai.gestures.background import pause_for_ptt

        if dest_file:
            destination = Path(dest_file).expanduser().absolute()
        else:
            directory = askai_data_dir() / "dictations"
            directory.mkdir(parents=True, exist_ok=True)
            destination = directory / f"dictation-{uuid4().hex}.txt"
        dictation.validate_destination(destination)
        instruction = msg.t("Dictating. Press Esc or pause for more than 3 seconds to finish and save.")

        def ready():
            text_formatter.commander_print(instruction)
            text_formatter.console.file.flush()

        from askai.core.component.multimedia.audio_player import player
        with pause_for_ptt():
            player.play_sfx('ui/dictate-start')
            _, original = recorder.listen(
                raise_on_timeout=False, raise_on_intelligible=False,
                counter_msg=msg.dictating(),
                end_silence=dictation.END_SILENCE_SECONDS, phrase_limit=0,
                finish_requested=finish_requested,
                wait_for_speech=True, on_ready=ready,
                on_captured=lambda: player.play_sfx('ui/dictate-end'),
            )
        if not original:
            text_formatter.commander_print(msg.t("Dictation produced no text!"))
            return
        source = dictation.save_original(destination, original)
        text_formatter.commander_print(msg.t("Original dictation saved:") + f" `{source}`")
        refined = dictation.refine(original, prompt.read_prompt("dictation-refiner.txt"), complete)
        dictation.save_refined(destination, refined)
        pyperclip.copy(refined)
        from askai.core.speech.dictation_memory import register
        from askai.core.support.persistent_memory import PersistentMemory

        durable = (PersistentMemory(askai_data_dir() / "memory" / "history.sqlite3")
                   if configs.is_keep_context else None)
        register(shared.memory, durable, configs.agent, Path.cwd(), source, destination, refined)
        text_formatter.commander_print(msg.t("Refined dictation saved and copied to the clipboard:") + f" `{destination}`")
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply
        events.reply.emit(reply=AIReply.final(f"<TTS>{refined}</TTS>"))
