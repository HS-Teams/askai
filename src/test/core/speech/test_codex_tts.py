import base64
from pathlib import Path
import tempfile
import unittest
import wave
from unittest.mock import Mock

from askai.core.agents.contracts import AgentError
from askai.core.speech.codex_tts import CodexTTS
from askai.core.speech.fallback_tts import FallbackTTS


class CodexSpeechTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'audio.wav'
        self.transport = Mock()
        self.transport.__enter__ = Mock(return_value=self.transport)
        self.transport.__exit__ = Mock(return_value=False)
        def request(method, params):
            return {
                'account/read': {'account': {'type': 'chatgpt'}},
                'thread/realtime/listVoices': {'voices': {'v2': ['marin'], 'defaultV2': 'marin'}},
                'thread/start': {'thread': {'id': 'speech'}},
            }.get(method, {})
        self.transport.request.side_effect = request
        self.cache = Mock()
        self.cache.audio_file_path.return_value = (self.path, False)
        self.settings = Mock()
        self.settings.get.return_value = None
        self.engine = CodexTTS(self.settings, self.cache, lambda: 1,
                               transport_factory=Mock(return_value=self.transport), timeout=.01)

    def events(self, success=True):
        return [
            {'method': 'thread/realtime/outputAudio/delta', 'params': {'threadId': 'speech', 'audio': {
                'sampleRate': 24000, 'numChannels': 1, 'data': base64.b64encode(b'\0\0' * 240).decode(),
            }}},
            ({'method': 'thread/realtime/transcript/done', 'params': {
                'threadId': 'speech', 'role': 'assistant', 'text': 'Olá!',
            }} if success else {'method': 'thread/realtime/itemAdded', 'params': {
                'threadId': 'speech', 'item': {'type': 'response.cancelled'},
            }}),
        ]

    def test_complete_audio_is_wav_and_cache_is_provider_scoped(self):
        self.transport.receive.side_effect = self.events()
        self.engine._voices = ['marin']
        self.engine._default_voice = 'marin'
        self.assertEqual(self.engine.synthesize('Olá!', playback=False), self.path)
        with wave.open(str(self.path)) as wav:
            self.assertEqual(wav.getnframes(), 240)
            self.assertEqual(wav.getframerate(), 24000)
        self.cache.audio_file_path.assert_called_once_with('Olá!', 'codex:codex-realtime-v2:marin', 'wav')
        self.transport.request.assert_any_call('thread/realtime/stop', {'threadId': 'speech'})
        self.cache.audio_file_path.return_value = (self.path, True)
        self.transport.request.reset_mock()
        self.engine.synthesize('Olá!', playback=False)
        self.transport.request.assert_not_called()

    def test_failed_partial_audio_does_not_publish_cache(self):
        self.transport.receive.side_effect = self.events(False)
        with self.assertRaises(AgentError):
            self.engine._generate('Olá!', None, self.path)
        self.assertFalse(self.path.exists())
        self.assertEqual(list(self.path.parent.iterdir()), [])

    def test_probe_requires_generation_not_cached_audio(self):
        self.transport.receive.side_effect = [{'method': 'thread/realtime/error',
                                               'params': {'threadId': 'speech', 'message': 'Unavailable'}}]
        with self.assertRaisesRegex(AgentError, 'Unavailable'):
            self.engine.probe()
        self.cache.audio_file_path.assert_not_called()

    def test_no_completion_times_out_without_audio_file(self):
        self.transport.receive.return_value = None
        with self.assertRaisesRegex(AgentError, 'timed out'):
            self.engine._generate('Olá!', None, self.path)
        self.assertFalse(self.path.exists())


class FallbackSpeechTests(unittest.TestCase):
    def setUp(self):
        self.primary, self.fallback, self.play = Mock(), Mock(), Mock()
        self.factory = Mock(return_value=self.fallback)
        self.engine = FallbackTTS(self.primary, self.factory, self.play)

    def test_startup_probes_once_and_uses_existing_fallback(self):
        self.primary.probe.side_effect = AgentError('Unavailable')
        self.assertEqual(self.engine.initialize(), 'Codex voice unavailable; using Ollama.')
        self.engine.initialize()
        self.primary.probe.assert_called_once()
        self.factory.assert_called_once()
        self.assertEqual(self.engine.voice, self.fallback.voice)
        self.engine.synthesize('Olá!', playback=False)
        self.fallback.synthesize.assert_called_once_with('Olá!', '', True, False, None)
        self.play.assert_not_called()

    def test_failure_after_startup_switches_once_without_replaying_partial_audio(self):
        self.engine.initialize()
        self.primary.synthesize.side_effect = AgentError('Disconnected')
        self.engine.synthesize('Olá!', voice='marin')
        self.fallback.synthesize.assert_called_once_with('Olá!', '', True, False, None)
        self.play.assert_called_once_with(self.fallback.synthesize.return_value)
        self.engine.synthesize('Again', playback=False)
        self.primary.synthesize.assert_called_once()

    def test_primary_success_does_not_instantiate_fallback(self):
        self.engine.synthesize('Olá!', playback=False)
        self.factory.assert_not_called()
        self.play.assert_not_called()

    def test_fallback_failure_is_reported_and_playback_failure_does_not_resynthesize(self):
        self.primary.probe.side_effect = AgentError('Unavailable')
        self.fallback.synthesize.side_effect = RuntimeError('Ollama unavailable')
        with self.assertRaisesRegex(RuntimeError, 'Ollama unavailable'):
            self.engine.synthesize('Olá!')
        self.play.assert_not_called()

    def test_playback_failure_does_not_invoke_fallback(self):
        self.play.side_effect = OSError('No audio device')
        with self.assertRaises(OSError):
            self.engine.synthesize('Olá!')
        self.factory.assert_not_called()
