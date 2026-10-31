# Speech engines

Speech capabilities are independent of the conversation agent selected with `-e`.
The public contracts live in `askai.core.speech.contracts` and use Python protocols.

- `STTEngine.transcribe(wav_audio: bytes, language: str) -> str` consumes a complete
  WAV recording. The caller owns microphone capture and presentation.
- `TTSEngine` exposes `model_name`, `voice`, `voices()`, `select_voice()` and
  `synthesize()`. Synthesis returns an audio file path, or `None` for empty text.
  A per-request voice override does not modify the saved voice. Failed synthesis
  raises an exception and must not populate the cache.

`SpeechService` lazily creates each capability separately. Application consumers
use `shared.speech.stt` and `shared.speech.tts`, independently of `shared.engine`.

## Configuration

| Capability | Environment variable | Default | Implemented providers |
| --- | --- | --- | --- |
| STT | `ASKAI_STT_ENGINE` | `google` | `google`, `whisper` |
| TTS | `ASKAI_TTS_ENGINE` | `auto` | `auto` (Codex → Ollama), `ollama` |

Set `ASKAI_STT_LANGUAGE=pt_BR` (or `askai.speech.stt.language`) to choose
the spoken language independently of the interface. Without an explicit speech
language, recognition uses the application language. Google receives a regional
tag such as `pt-BR`; local Whisper receives the language code `pt`.

The corresponding settings are `askai.speech.stt.engine` and
`askai.speech.tts.engine`. Unsupported providers raise an error. The `auto` strategy explicitly uses
Ollama when the Codex voice probe or subsequent synthesis fails. Whisper requires its local recognition dependencies.

Ollama uses the existing Phonon implementation, voice selection and audio cache.
Its cache identity includes endpoint, model, voice and text. `/speak` controls
whether the final answer is spoken.

## Adding a provider

Implement the applicable protocol and add its construction to the corresponding
factory in `askai.core.speech.factory`. A provider can implement STT, TTS or both;
it does not need to implement a conversation agent. Keep credentials and
provider-specific options in the adapter. Add tests for input/output, errors,
voice overrides and cache behavior where applicable.

ElevenLabs is a planned adapter, not an implemented provider.

## Automatic Codex voice selection

CLI and TUI startup generate a short, silent test sample through the experimental
Codex app-server realtime V2 interface. Listing voices alone is not sufficient.
The probe bypasses the audio cache and does not capture the microphone or play
sound. It uses an ephemeral, read-only thread separate from the conversation,
with ChatGPT authentication and bounded transport/audio waits.

If generation fails, the existing Ollama/Phonon adapter is selected for the rest
of that process. Its saved voice, model and audio cache remain unchanged. Startup
reports the selected strategy; diagnostic details are available in debug logs.
A new application startup tries Codex again. Explicit `ASKAI_TTS_ENGINE=ollama`
skips the Codex probe. A later Codex synthesis failure also selects Ollama; errors
from Ollama or audio playback still surface rather than causing repeated attempts.

Codex WAV cache keys include provider, protocol/model identity, voice and text.
Incomplete output is never published to the cache or played. Voice selection
uses the runtime's returned list and is stored separately from Phonon's voice.

The local integration test on 2026-10-31 listed Codex voices successfully, but
its realtime websocket closed before generating audio. The automatic fallback
then generated a valid 1.28-second Phonon WAV for “Olá!”. Successful Codex audio
remains unverified with this account; protocol handling is covered by mocked
notification tests, including completion, cancellation, timeout and caching.

## Concurrent output and synchronized presentation

Speech synthesis runs in a bounded, ordered output worker. With `/speak` on,
the final answer is presented progressively alongside playback, then retains its
formatted Markdown. Progress uses the generated WAV duration, playback tempo and
measured player startup delay; it is approximate timing, not word-level alignment
metadata from the speech provider. CLI input waits for presentation to finish;
Textual presentation updates are dispatched onto its UI thread.

New requests, microphone capture and Ctrl+C cancel pending speech and stop only
the queue's own ffplay process. An already-running provider synthesis can finish
and populate its cache, but cancelled audio is not played. Shutdown waits for that
bounded provider operation to finish. Failures are reported without recursively
trying to speak the error. Music playback is independent of this queue.
