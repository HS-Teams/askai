"""Existing Ollama speech preferences, independent of the selected agent."""

import os
from askai.core.askai_configs import AskAiConfigs
from askai.core.askai_settings import settings


class LlamaConfigs(AskAiConfigs):
    @property
    def base_url(self) -> str:
        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        return host if "://" in host else f"http://{host}"

    @property
    def timeout(self) -> float:
        value = float(os.getenv("ASKAI_LLAMA_TIMEOUT", "120"))
        if value <= 0:
            raise ValueError("ASKAI_LLAMA_TIMEOUT must be positive")
        return value

    @property
    def tts_model(self) -> str:
        return os.getenv("ASKAI_LLAMA_TTS_MODEL", "phonon")

    @property
    def tts_voice(self) -> str:
        return settings.get("askai.llama.text.to.speech.voice") or "Grub the Ogre"

    @tts_voice.setter
    def tts_voice(self, value: str) -> None:
        settings.put("askai.llama.text.to.speech.voice", value)
