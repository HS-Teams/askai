"""ElevenLabs synthesis with complete WAV publication and shared audio caching."""
from hashlib import sha256
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import RLock
from urllib.parse import quote
import wave

import requests
from askai.core.agents.contracts import AgentError
from askai.core.speech.audio_tags import strip_audio_tags


class ElevenLabsTTS:
    provider_name = 'ElevenLabs'
    SAMPLE_RATE = 24000
    PROBE_TEXT = 'Olá!'

    def __init__(self, settings, cache, tempo, request=requests.request):
        self._settings, self._cache, self._tempo = settings, cache, tempo
        self._request = request
        self._default_voice = None
        self._voices = None
        self._lock = RLock()

    @property
    def model_name(self):
        return self._settings.get('askai.elevenlabs.tts.model') or 'eleven_v4'

    def _speech_text(self, text):
        if self.model_name in {'eleven_v4', 'eleven_v4_turbo', 'eleven_v3'}:
            return text
        return strip_audio_tags(text)

    @property
    def voice(self):
        return self._settings.get('askai.elevenlabs.tts.voice') or ''

    @property
    def voice_name(self):
        if not self.voice:
            return ''
        for label, voice_id in (self._voices or {}).items():
            if voice_id == self.voice:
                return label.removesuffix(f' [{voice_id}]')
        return self.voice

    def _call(self, method, endpoint, **kwargs):
        key = os.getenv('ELEVENLABS_API_KEY')
        if not key:
            raise AgentError('ELEVENLABS_API_KEY is not configured')
        try:
            response = self._request(method, 'https://api.elevenlabs.io' + endpoint,
                                     headers={'xi-api-key': key}, timeout=(5, 45),
                                     allow_redirects=False, **kwargs)
        except requests.RequestException:
            raise AgentError('ElevenLabs connection failed') from None
        if response.status_code != 200:
            reasons = {
                'quota_exceeded': 'ElevenLabs credits exhausted',
                'paid_plan_required': 'This ElevenLabs voice or model requires a paid plan',
                'invalid_api_key': 'Invalid ElevenLabs API key',
                'missing_permissions': 'ElevenLabs API key lacks permission',
                'too_many_concurrent_requests': 'ElevenLabs concurrent request limit reached',
                'rate_limit_exceeded': 'ElevenLabs request rate limit reached',
            }
            reason = 'ElevenLabs request failed'
            try:
                payload = response.json()
                detail = payload.get('detail') if isinstance(payload, dict) else None
                if isinstance(detail, dict):
                    code = detail.get('code') or detail.get('status')
                    reason = reasons.get(code, reason)
            except ValueError:
                pass
            response.close()
            raise AgentError(f'{reason} (HTTP {response.status_code})')
        return response

    def voices(self):
        with self._lock:
            if self._voices is None:
                voices, token = {}, None
                while True:
                    params = {'page_size': 100, 'sort': 'name', 'sort_direction': 'asc'}
                    if token:
                        params['next_page_token'] = token
                    with self._call('GET', '/v2/voices', params=params) as response:
                        page = response.json()
                    for voice in page['voices']:
                        voices[f"{voice['name']} [{voice['voice_id']}]"] = voice['voice_id']
                        if self._default_voice is None and voice.get('category') == 'premade':
                            self._default_voice = voice['voice_id']
                    if not page.get('has_more'):
                        break
                    next_token = page.get('next_page_token')
                    if not next_token or next_token == token:
                        raise AgentError('Invalid ElevenLabs voice pagination')
                    token = next_token
                if not voices:
                    raise AgentError('No ElevenLabs voices available')
                self._voices = voices
            return sorted(self._voices, key=str.casefold)

    def refresh_voices(self):
        with self._lock:
            self._voices = None
            self._default_voice = None
            return self.voices()

    def select_voice(self, voice):
        self.voices()
        selected = self._voices.get(voice, voice)
        if selected not in self._voices.values():
            raise ValueError('Unknown ElevenLabs voice')
        self._settings.put('askai.elevenlabs.tts.voice', selected)

    def usage(self):
        from askai.core.support.usage import elevenlabs_usage

        with self._call('GET', '/v1/user/subscription') as response:
            return elevenlabs_usage(response.json())

    def probe(self):
        if not self.voice:
            self.voices()
            if not self._default_voice:
                raise AgentError("Select an ElevenLabs voice before synthesis")
            self.select_voice(self._default_voice)
        # A real, tiny request at setup validates authentication, voice and quota.
        with NamedTemporaryFile(suffix='.wav') as sample:
            self._generate(self.PROBE_TEXT, self.voice, Path(sample.name))
        if self._voices is None:
            import logging

            try:
                self.voices()
            except (AgentError, OSError, ValueError, KeyError, TypeError) as error:
                logging.warning('Could not load ElevenLabs voice names: %s', error)

    def _path(self, text, voice):
        identity = f'elevenlabs:{self.model_name}:{voice}:pcm_{self.SAMPLE_RATE}:' + sha256(text.encode()).hexdigest()
        filename, exists = self._cache.audio_file_path(text, identity, 'wav')
        return Path(filename), exists

    def cached_audio(self, text, voice=None):
        text = self._speech_text(text)
        selected = self._selected_voice(voice)
        path, exists = self._path(text, selected)
        return path if exists else None

    def _selected_voice(self, voice):
        return (self._voices or {}).get(voice, voice) if voice else self.voice

    def synthesize(self, text, prefix='', stream=True, playback=True, voice=None):
        text = self._speech_text(text)
        if not strip_audio_tags(text).strip():
            return None
        selected = self._selected_voice(voice)
        if not selected:
            raise AgentError('No ElevenLabs voice selected')
        with self._lock:
            path, exists = self._path(text, selected)
            if not exists:
                self._generate(text, selected, path)
        if playback:
            from askai.core.component.multimedia.audio_player import player
            from askai.core.support.cache_policy import release_transient_audio
            try:
                player.play_audio_file(path, self._tempo())
            finally:
                release_transient_audio(path)
        return path

    def speak_live(self, text, cancelled, tempo):
        from askai.core.speech.playback import play_speech
        from askai.core.speech.pcm_stream import play_pcm_chunks

        text = self._speech_text(text)
        if not strip_audio_tags(text).strip():
            return None
        with self._lock:
            path, exists = self._path(text, self.voice)
            if exists:
                play_speech(path, tempo, cancelled)
                return path
            with self._call('POST', '/v1/text-to-speech/' + quote(self.voice, safe='') + '/stream',
                            params={'output_format': f'pcm_{self.SAMPLE_RATE}'},
                            json={'text': text, 'model_id': self.model_name}, stream=True) as response:
                content_type = response.headers.get('Content-Type', '').split(';')[0]
                if not (content_type.startswith('audio/') or content_type == 'application/octet-stream'):
                    raise AgentError('ElevenLabs did not return audio')
                try:
                    audio = play_pcm_chunks(response.iter_content(chunk_size=1024), self.SAMPLE_RATE, tempo, cancelled)
                except requests.RequestException:
                    raise AgentError('ElevenLabs stream connection failed') from None
            if audio is None:
                return None
            self._write_pcm(audio, path)
            return path

    def _generate(self, text, voice, path):
        with self._call('POST', '/v1/text-to-speech/' + quote(voice, safe=''),
                        params={'output_format': f'pcm_{self.SAMPLE_RATE}'},
                        json={'text': text, 'model_id': self.model_name}) as response:
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            audio = response.content
        if not (content_type.startswith('audio/') or content_type == 'application/octet-stream'):
            raise AgentError('ElevenLabs did not return audio')
        if not audio or len(audio) % 2:
            raise AgentError('ElevenLabs returned incomplete PCM audio')
        self._write_pcm(audio, path)

    def _write_pcm(self, audio, path):
        with NamedTemporaryFile(dir=path.parent, suffix='.wav', delete=False) as temporary:
            staging = Path(temporary.name)
            try:
                with wave.open(str(staging), 'wb') as output:
                    output.setnchannels(1)
                    output.setsampwidth(2)
                    output.setframerate(self.SAMPLE_RATE)
                    output.writeframes(audio)
                staging.replace(path)
            finally:
                staging.unlink(missing_ok=True)
