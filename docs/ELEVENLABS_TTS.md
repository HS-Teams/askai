# ElevenLabs speech

`askai.speech.tts.engine` is the existing provider setting. Its default is now
`ElevenLabs`; `Ollama` selects local synthesis directly. `ASKAI_TTS_ENGINE` still
has precedence. Restart AskAI after changing the provider.

```text
/settings set askai.speech.tts.engine ElevenLabs
/settings set askai.elevenlabs.tts.model eleven_v4
/voices list
/voices set "Name [voice_id]"
```

Set `ELEVENLABS_API_KEY` in the application's environment. The key is not stored
in settings. The default model is Eleven v4. Existing saved model selections are
retained; use the command above to switch them to v4. The initial voice is
chosen from the account's premade voices and persisted; an explicit voice choice
is never replaced automatically.

The existing startup speech check performs one tiny synthesis ("Olá!") without
playing it. This is a real API request and consumes credits. It intentionally
bypasses cache to check authentication, voice access and remaining quota.

Normal synthesis checks the existing audio cache first. Its identity includes
provider, model, voice, exact text and audio format. Only complete WAV files are
published atomically. Concurrent identical requests reuse the completed audio.
Cache OFF continues to disable reuse and uses transient audio files.

A failed startup probe or later synthesis switches to Ollama for the rest of the
process, avoiding repeated failed API requests until an explicit voice selection. Cached ElevenLabs audio remains
usable during fallback. `/voices list` and `/voices play` always target the configured provider, even
during fallback. `/voices set` saves the selection and performs a small real
synthesis probe; success restores ElevenLabs immediately, without restarting.
Failure keeps Ollama active and reports the cause. Selecting the current voice
also retries it. Restarting retries ElevenLabs as well.
Ollama keeps its own saved voice. Playback errors do not trigger another paid
synthesis. Each switch to fallback emits a translated system warning with its reason, separate
from assistant responses and never synthesized. The cause is also logged at WARNING
level. The configured default remains ElevenLabs; only the active provider changes.

The CLI status and TUI tooltip show `TTS Engine: ElevenLabs` or
`TTS Engine: Ollama (fallback)` to distinguish the configured and active providers.
STT, text/audio synchronization and speech tempo are unchanged.

## Expressive narration

Codex is asked to optionally suggest sparse delivery cues. The response refiner
preserves applicable cues inside its `<TTS>` passage without inventing any. If
Codex supplies none, synthesis proceeds with natural delivery:

```text
<TTS>[happy] Que bom ter voce por aqui! [curious] Como posso ajudar?</TTS>
```

Supported cues are `[happy]`, `[sad]`, `[angry]`, `[curious]`, `[excited]`,
`[crying]`, `[mischievously]`, `[whispers]`, `[shouts]`, `[laughs]`,
`[clears throat]` and `[sighs]`. Cues are preserved in translation and sent
unchanged to Eleven v4 in both ordinary and live synthesis. They are hidden
from the visual narration. Exact dictations and quotations must retain their wording.
Eleven v3 and v4 Turbo also receive the cues; other configured ElevenLabs models
and Ollama omit them so unsupported engines do not read the directions aloud.
The cache distinguishes different delivery cues and models. Voice choice and
context affect the resulting delivery.

Restart AskAI after updating, configure `ELEVENLABS_API_KEY`, select `eleven_v4`
if a different model was saved, and enable `/speak` for spoken responses.

Audio tag reference: https://elevenlabs.io/docs/help-center/product/core-capabilities/text-to-speech/how-do-audio-tags-work-with-eleven-v3-and-v4.

API references: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
and https://elevenlabs.io/docs/api-reference/voices/search.
