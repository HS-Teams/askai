"""Factories for independent STT and TTS capabilities; no agent dependency."""

from askai.core.speech.contracts import STTEngine, TTSEngine


def create_stt(name: str) -> STTEngine:
    from askai.core.speech.recognizer_stt import RecognizerSTT

    return RecognizerSTT(name.strip().casefold())


def create_tts(name: str) -> TTSEngine:
    if name.strip().casefold() in {"auto", "elevenlabs"}:
        from askai.core.askai_events import events
        from askai.core.askai_configs import configs
        from askai.core.askai_settings import settings
        from askai.core.component.cache_service import cache
        from askai.core.component.multimedia.audio_player import player
        from askai.core.speech.elevenlabs_tts import ElevenLabsTTS
        from askai.core.speech.fallback_tts import FallbackTTS

        return FallbackTTS(
            ElevenLabsTTS(settings, cache, lambda: configs.tempo),
            lambda: create_tts("ollama"),
            lambda path: player.play_audio_file(path, configs.tempo),
            notify=lambda provider, reason: events.tts_fallback.emit(provider=provider, reason=reason),
        )
    if name.strip().casefold() != "ollama":
        raise ValueError(f"TTS engine '{name}' is not implemented. Available: auto, elevenlabs, ollama.")
    from askai.core.engine.llama.llama_configs import LlamaConfigs
    from askai.core.engine.llama.llama_speech import LlamaSpeech
    from askai.core.engine.llama.ollama_client import OllamaClient

    configs = LlamaConfigs()
    return LlamaSpeech(OllamaClient(configs.base_url, configs.timeout), configs)
