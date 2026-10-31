#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
   @project: HsPyLib-AskAI
   @package: askai.core.askai_configs
      @file: askai_configs.py
   @created: Fri, 5 Jan 2024
    @author: <B>H</B>ugo <B>S</B>aporetti <B>J</B>unior
      @site: https://github.com/yorevs/askai
   @license: MIT - Please refer to <https://opensource.org/licenses/MIT>

   Copyright (c) 2024, AskAI
"""
from askai.__classpath__ import classpath
from askai.core.askai_settings import settings
from askai.core.enums.acc_color import AccColor
from askai.core.enums.verbosity import Verbosity
from askai.language.language import Language
from hspylib.core.enums.charset import Charset
from hspylib.core.metaclass.singleton import Singleton
from shutil import which

import os


class AskAiConfigs(metaclass=Singleton):
    """Provides access to AskAI configurations."""

    # The resources folder
    RESOURCE_DIR = str(classpath.resource_path)

    def __init__(self):
        self._recorder_devices: set[str] = set(map(str.strip, settings.get_list("askai.recorder.devices")))

    @property
    def stt_engine(self) -> str:
        return os.getenv("ASKAI_STT_ENGINE") or settings.get("askai.speech.stt.engine") or "google"

    @property
    def stt_language(self) -> Language:
        value = os.getenv("ASKAI_STT_LANGUAGE") or settings.get("askai.speech.stt.language")
        return Language.of_locale(value) if value else self.language

    @property
    def tts_engine(self) -> str:
        return os.getenv("ASKAI_TTS_ENGINE") or settings.get("askai.speech.tts.engine") or "ElevenLabs"

    @property
    def compact_on_exit(self) -> bool:
        return settings.get_bool("askai.session.compact.on.exit", True)

    @property
    def agent(self) -> str:
        return settings.get("askai.agent.default").strip() or "codex"

    @agent.setter
    def agent(self, value: str) -> None:
        settings.put("askai.agent.default", value)

    @property
    def engine(self) -> str:
        return settings.get("askai.default.engine")

    @engine.setter
    def engine(self, value: str) -> None:
        settings.put("askai.default.engine", value)

    @property
    def model(self) -> str | None:
        return self.model_for(self.engine)

    @model.setter
    def model(self, value: str) -> None:
        settings.put(f"askai.{self.engine}.default.model", value)

    def model_for(self, engine: str) -> str | None:
        """Return this engine's saved model, or let its factory choose the default."""
        return settings.get(f"askai.{engine}.default.model").strip() or None

    @property
    def is_interactive(self) -> bool:
        return settings.get_bool("askai.interactive.enabled")

    @is_interactive.setter
    def is_interactive(self, value: bool) -> None:
        settings.put("askai.interactive.enabled", value)

    @property
    def is_speak(self) -> bool:
        return which("ffplay") and settings.get_bool("askai.speak.enabled")

    @is_speak.setter
    def is_speak(self, value: bool) -> None:
        settings.put("askai.speak.enabled", which("ffplay") and value)

    @property
    def is_debug(self) -> bool:
        return settings.get_bool("askai.debug.enabled")

    @is_debug.setter
    def is_debug(self, value: bool) -> None:
        settings.put("askai.debug.enabled", value)

    @property
    def is_cache(self) -> bool:
        return settings.get_bool("askai.cache.enabled")

    @is_cache.setter
    def is_cache(self, value: bool) -> None:
        settings.put("askai.cache.enabled", value)

    @property
    def is_keep_context(self) -> bool:
        return settings.get_bool("askai.context.keep.conversation")

    @is_keep_context.setter
    def is_keep_context(self, value: bool) -> None:
        settings.put("askai.context.keep.conversation", value)

    @property
    def tempo(self) -> int:
        return settings.get_int("askai.text.to.speech.tempo")

    @tempo.setter
    def tempo(self, value: int) -> None:
        settings.put("askai.text.to.speech.tempo", value)

    @property
    def ttl(self) -> int:
        return settings.get_int("askai.cache.ttl.minutes")

    @ttl.setter
    def ttl(self, value: int) -> None:
        settings.put("askai.cache.ttl.minutes", value)

    @property
    def verbosity(self) -> Verbosity:
        return Verbosity.of_value(settings.get_int("askai.verbosity.level"))

    @property
    def chunk_size(self) -> int:
        return settings.get_int("askai.text.splitter.chunk.size")

    @property
    def chunk_overlap(self) -> int:
        return settings.get_int("askai.text.splitter.chunk.overlap")

    @property
    def rag_retrival_amount(self) -> int:
        return settings.get_int("askai.rag.retrival.amount")

    @property
    def is_rag(self) -> bool:
        return settings.get_bool("askai.rag.enabled")

    @is_rag.setter
    def is_rag(self, value: bool) -> None:
        settings.put("askai.rag.enabled", value)

    @property
    def ip_api_enabled(self) -> bool:
        return settings.get_bool("askai.ip-api.geo-location.enabled")

    @ip_api_enabled.setter
    def ip_api_enabled(self, value: bool) -> None:
        settings.put("askai.ip-api.geo-location.enabled", value)

    @property
    def is_assistive(self) -> bool:
        return settings.get_bool("askai.router.assistive.enabled")

    @is_assistive.setter
    def is_assistive(self, value: bool) -> None:
        settings.put("askai.router.assistive.enabled", value)

    @property
    def language(self) -> Language:
        # Lookup order: Settings -> Locale -> Environment.
        try:
            lang: Language = Language.of_locale(
                settings.get("askai.preferred.language")
                or os.getenv("LC_ALL", os.getenv("LC_TYPE", os.getenv("LANG")))
                or Language.EN_US.idiom
            )
        except ValueError:
            lang: Language = Language.EN_US

        return lang

    @property
    def default_router_mode(self) -> str:
        return settings.get("askai.router.mode.default")

    @property
    def pass_threshold(self) -> AccColor:
        try:
            color: AccColor = AccColor.value_of(settings.get("askai.router.pass.threshold"))
        except ValueError:
            color: AccColor = AccColor.MODERATE

        return color

    @property
    def encoding(self) -> Charset:
        return self.language.encoding

    @property
    def max_iteractions(self) -> int:
        return settings.get_int("askai.max.router.iteractions")

    @property
    def max_short_memory_size(self) -> int:
        return settings.get_int("askai.max.short.memory.size")

    @property
    def max_router_retries(self) -> int:
        return settings.get_int("askai.max.router.retries")

    @property
    def max_agent_retries(self) -> int:
        return settings.get_int("askai.max.agent.retries")

    @property
    def max_agent_execution_time_seconds(self) -> int:
        return settings.get_int("askai.max.agent.execution.time.seconds")

    @property
    def identity_similarity_threshold(self) -> float:
        from askai.core.component.faces.models import DEFAULT_THRESHOLD
        return settings.get_float("askai.camera.identity.sface.cosine.threshold", DEFAULT_THRESHOLD)

    @property
    def identity_caption_enabled(self) -> bool:
        return settings.get_bool("askai.camera.identity.caption.enabled", False)

    @property
    def recorder_phrase_limit_millis(self) -> int:
        return settings.get_int("askai.recorder.phrase.limit.millis")

    @property
    def recorder_tail_margin_millis(self) -> int:
        value = settings.get("askai.recorder.tail.margin.millis")
        return int(value) if value else 1500

    @property
    def recorder_end_silence_millis(self) -> int:
        value = settings.get("askai.recorder.end.silence.millis")
        return int(value) if value else 2000

    @property
    def recorder_silence_timeout_millis(self) -> int:
        return settings.get_int("askai.recorder.silence.timeout.millis")

    @property
    def recorder_noise_detection_duration_millis(self) -> int:
        return settings.get_int("askai.recorder.noise.detection.duration.millis")

    @property
    def recorder_input_device_auto_swap(self) -> bool:
        return settings.get_bool("askai.recorder.input.device.auto.swap")

    @property
    def recorder_devices(self) -> set[str]:
        return self._recorder_devices

    def add_device(self, device_name: str) -> None:
        """Add a new device to the configuration list.
        :param device_name: The device name to be added.
        """
        if device_name not in self._recorder_devices:
            self._recorder_devices.add(device_name)
            settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))

    def remove_device(self, device_name: str) -> None:
        """Remove a new device from the configuration list.
        :param device_name: The device name to be removed.
        """
        if device_name in self._recorder_devices:
            self._recorder_devices.remove(device_name)
            settings.put("askai.recorder.devices", ", ".join(self._recorder_devices))

    def clear_devices(self) -> None:
        """Remove all devices from the configuration list."""
        self._recorder_devices.clear()


assert (configs := AskAiConfigs()) is not None
