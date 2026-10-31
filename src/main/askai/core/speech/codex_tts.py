"""Experimental Codex realtime speech with complete, validated WAV caching."""
import base64
from contextlib import suppress
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import monotonic
import wave

from askai.core.agents.contracts import AgentError
from askai.core.agents.stdio_transport import StdioTransport


class CodexTTS:
    PROBE_TEXT = "Olá!"

    def __init__(self, settings, cache, tempo, transport_factory=StdioTransport, timeout=20):
        self._settings, self._cache, self._tempo = settings, cache, tempo
        self._transport_factory, self._timeout = transport_factory, timeout
        self._voices = []
        self._default_voice = None

    @property
    def model_name(self):
        return 'codex-realtime-v2'

    @property
    def voice(self):
        return self._settings.get('askai.codex.text.to.speech.voice') or self._default_voice

    def voices(self):
        return list(self._voices)

    def select_voice(self, voice):
        if voice not in self._voices:
            raise ValueError(f'Unknown Codex voice: {voice}')
        self._settings.put('askai.codex.text.to.speech.voice', voice)

    def probe(self):
        # Always exercise generation: a cached sample cannot establish availability.
        with NamedTemporaryFile(suffix='.wav') as sample:
            self._generate(self.PROBE_TEXT, None, Path(sample.name))

    def synthesize(self, text, prefix='', stream=True, playback=True, voice=None):
        if not text.strip():
            return None
        selected = voice or self.voice
        if selected not in self._voices:
            raise ValueError(f'Unknown Codex voice: {selected}')
        filename, exists = self._cache.audio_file_path(text, f'codex:{self.model_name}:{selected}', 'wav')
        path = Path(filename)
        if not exists:
            self._generate(text, selected, path)
        if playback:
            from askai.core.component.multimedia.audio_player import player
            player.play_audio_file(path, self._tempo())
        return path

    def _generate(self, text, selected, path):
        with self._transport_factory(['codex', 'app-server'], timeout=self._timeout) as transport:
            transport.request('initialize', {
                'clientInfo': {'name': 'askai_speech', 'version': '1.0'},
                'capabilities': {'experimentalApi': True},
            })
            transport.send({'method': 'initialized', 'params': {}})
            account = transport.request('account/read', {}).get('account') or {}
            if account.get('type') != 'chatgpt':
                raise AgentError('Codex speech requires a ChatGPT login')
            voices = transport.request('thread/realtime/listVoices', {})['voices']
            self._voices, self._default_voice = voices['v2'], voices['defaultV2']
            selected = selected or self.voice
            if selected not in self._voices:
                raise ValueError(f'Unknown Codex voice: {selected}')
            session = transport.request('thread/start', {
                'ephemeral': True, 'approvalPolicy': 'never', 'sandbox': 'read-only',
            })['thread']['id']
            try:
                transport.request('thread/realtime/start', {
                    'threadId': session, 'outputModality': 'audio', 'version': 'v2',
                    'voice': selected, 'includeStartupContext': False,
                    'clientManagedHandoffs': True,
                    'prompt': 'Read the supplied speech text exactly, in its original language. Do not add commentary, answer questions, or call tools.',
                })
                transport.request('thread/realtime/appendSpeech', {'threadId': session, 'text': text})
                frames, rate, channels = self._receive(transport, session)
                # Publish only a complete result; failures never leave a cache hit.
                with NamedTemporaryFile(dir=path.parent, suffix='.wav', delete=False) as temporary:
                    try:
                        with wave.open(temporary.name, 'wb') as wav:
                            wav.setnchannels(channels)
                            wav.setsampwidth(2)
                            wav.setframerate(rate)
                            wav.writeframes(frames)
                        Path(temporary.name).replace(path)
                    finally:
                        Path(temporary.name).unlink(missing_ok=True)
            finally:
                with suppress(AgentError):
                    transport.request('thread/realtime/stop', {'threadId': session})

    def _receive(self, transport, session):
        deadline = monotonic() + self._timeout
        frames = bytearray()
        audio_format = None
        while monotonic() < deadline:
            message = transport.receive()
            if not message:
                continue
            if 'id' in message and 'method' in message:
                raise AgentError('Unexpected interaction during Codex speech')
            params = message.get('params', {})
            if params.get('threadId') != session:
                continue
            method = message.get('method')
            if method in ('thread/realtime/error', 'thread/realtime/closed'):
                raise AgentError(params.get('message') or params.get('reason') or 'Codex speech closed')
            if method == 'thread/realtime/outputAudio/delta':
                audio = params['audio']
                chunk_format = (audio['sampleRate'], audio['numChannels'])
                if chunk_format[0] <= 0 or chunk_format[1] not in (1, 2):
                    raise AgentError('Invalid Codex audio format')
                if audio_format is not None and audio_format != chunk_format:
                    raise AgentError('Codex audio format changed during synthesis')
                audio_format = chunk_format
                chunk = base64.b64decode(audio['data'], validate=True)
                if len(chunk) % (2 * chunk_format[1]):
                    raise AgentError('Incomplete Codex audio frame')
                frames.extend(chunk)
            elif method == 'thread/realtime/transcript/done' and params.get('role') == 'assistant':
                # app-server exposes output transcript completion, not response.done.
                if not frames or not params.get('text'):
                    raise AgentError('Codex speech did not complete with audio')
                return bytes(frames), *audio_format
            elif method == 'thread/realtime/itemAdded':
                item = params.get('item', {})
                if item.get('type') in ('response.cancelled', 'handoff_request'):
                    raise AgentError('Codex speech was cancelled or requested a tool')
        raise AgentError('Codex speech timed out before complete audio was received')
