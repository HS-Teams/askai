import base64
from hashlib import sha256
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import wave

from askai.core.agents.contracts import AgentError
from askai.core.speech.elevenlabs_tts import ElevenLabsTTS
from askai.core.speech.fallback_tts import FallbackTTS


class ElevenLabsTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.values = {'askai.elevenlabs.tts.voice': 'voice1'}
        self.settings = Mock()
        self.settings.get.side_effect = lambda key: self.values.get(key)
        self.settings.put.side_effect = self.values.__setitem__
        self.cache = Mock()
        self.cache.audio_file_path.side_effect = self.cache_path
        self.request = Mock()
        self.response = Mock(status_code=200, headers={'Content-Type': 'audio/pcm'}, content=b'\x00\x01' * 240)
        self.response.__enter__ = Mock(return_value=self.response)
        self.response.__exit__ = Mock(return_value=False)
        self.request.return_value = self.response
        self.response.json.return_value = {'audio_base64': base64.b64encode(self.response.content).decode(), 'alignment': None}
        self.engine = ElevenLabsTTS(self.settings, self.cache, lambda: 1, self.request)
        self.env = patch.dict(os.environ, {'ELEVENLABS_API_KEY': 'test-secret'})
        self.env.start()
        self.addCleanup(self.env.stop)

    def cache_path(self, text, identity, extension):
        path = self.root / (sha256((text + identity).encode()).hexdigest() + '.' + extension)
        return str(path), path.exists()

    def test_display_name_resolves_selected_id_without_changing_synthesis_voice(self):
        self.response.json.return_value = {'voices': [{'name': 'Friendly Voice', 'voice_id': 'voice1'}], 'has_more': False}
        self.engine.voices()
        self.assertEqual(self.engine.voice_name, 'Friendly Voice')
        self.assertEqual(self.engine.voice, 'voice1')
        self.assertEqual(self.engine.voice_name, 'Friendly Voice')
        self.request.assert_called_once()

    def test_display_name_uses_id_without_network_when_catalogue_is_unavailable(self):
        self.request.side_effect = OSError('offline')
        self.assertEqual(self.engine.voice_name, 'voice1')
        self.engine._voices = {'Other [other]': 'other'}
        self.assertEqual(self.engine.voice_name, 'voice1')
        self.request.assert_not_called()

    def test_local_active_voice_name_is_preserved_during_fallback(self):
        primary = Mock()
        primary.probe.side_effect = AgentError('offline')
        from types import SimpleNamespace
        local = SimpleNamespace(voice='Grub the Ogre')
        wrapper = FallbackTTS(primary, lambda: local, Mock())
        self.assertEqual(wrapper.voice_name, 'Grub the Ogre')

    def test_v4_is_default_and_preserves_delivery_cues_with_distinct_cache(self):
        self.assertEqual(self.engine.model_name, 'eleven_v4')
        text = '[happy] Ola!'
        happy = self.engine.synthesize(text, playback=False)
        self.assertEqual(self.request.call_args.kwargs['json'], {'text': text, 'model_id': 'eleven_v4'})
        sad = self.engine.synthesize('[sad] Ola!', playback=False)
        self.assertNotEqual(happy, sad)

    def test_nonexpressive_model_omits_only_known_cues(self):
        self.values['askai.elevenlabs.tts.model'] = 'eleven_flash_v2_5'
        self.engine.synthesize('[happy]Use [filename].', playback=False)
        self.assertEqual(self.request.call_args.kwargs['json']['text'], 'Use [filename].')

    def test_cues_alone_do_not_generate_audio(self):
        from threading import Event
        self.assertIsNone(self.engine.synthesize('[happy]', playback=False))
        self.assertIsNone(self.engine.speak_live('[happy]', Event(), 1))
        self.request.assert_not_called()

    def test_repeated_text_uses_cache_and_model_voice_case_are_distinct(self):
        path = self.engine.synthesize('Olá API', playback=False)
        self.assertEqual(self.engine.synthesize('Olá API', playback=False), path)
        self.request.assert_called_once()
        with wave.open(str(path)) as audio:
            self.assertEqual(audio.getframerate(), 24000)
        self.engine.synthesize('Olá api', playback=False)
        self.engine.synthesize('Olá API', voice='voice2', playback=False)
        self.values['askai.elevenlabs.tts.model'] = 'eleven_multilingual_v2'
        self.engine.synthesize('Olá API', playback=False)
        self.assertEqual(self.request.call_count, 4)
        self.assertEqual(self.engine.voice, 'voice1')

    def test_probe_is_real_and_does_not_play_or_publish_cache(self):
        self.response.json.return_value = {'voices': [{'name': 'Voice', 'voice_id': 'voice1'}], 'has_more': False, 'audio_base64': base64.b64encode(self.response.content).decode()}
        self.engine.probe()
        self.assertEqual([call.args[0] for call in self.request.call_args_list], ['POST', 'GET'])
        self.cache.audio_file_path.assert_not_called()
        self.assertEqual(list(self.root.iterdir()), [])

    def test_quota_failure_switches_to_ollama_and_still_serves_cached_primary_audio(self):
        path = self.engine.synthesize('cached', playback=False)
        self.response.status_code = 401
        fallback = Mock()
        wrapper = FallbackTTS(self.engine, lambda: fallback, Mock())
        wrapper.initialize()
        count = self.request.call_count
        self.assertEqual(wrapper.provider_name, 'Ollama (fallback)')
        self.assertEqual(wrapper.synthesize('cached', playback=False), path)
        fallback.synthesize.assert_not_called()
        wrapper.synthesize('new', playback=False, voice='voice1')
        fallback.synthesize.assert_called_once_with('new', '', True, False, None)
        self.assertEqual(self.request.call_count, count)

    def test_bad_responses_never_publish_cache(self):
        for status, content_type, audio in ((429, 'audio/pcm', b'ab'), (200, 'application/json', b'{}'),
                                             (200, 'audio/pcm', b'x'), (200, 'audio/pcm', b'')):
            self.response.status_code = status
            self.response.headers['Content-Type'] = content_type
            self.response.content = audio
            self.response.json.return_value = ({'audio_base64': base64.b64encode(audio).decode()}
                                               if content_type != 'application/json' else {})
            with self.assertRaises(AgentError):
                self.engine.synthesize('text', playback=False)
            self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_key_and_connection_failure_do_not_expose_secret(self):
        import requests
        self.request.side_effect = requests.Timeout('test-secret')
        with self.assertRaises(AgentError) as failure:
            self.engine.probe()
        self.assertNotIn('test-secret', str(failure.exception))
        with patch.dict(os.environ, {'ELEVENLABS_API_KEY': ''}):
            with self.assertRaises(AgentError):
                self.engine.probe()

    def test_voice_catalog_and_selection(self):
        self.response.json.return_value = {'voices': [{'name': 'Voice', 'voice_id': 'v'}], 'has_more': False}
        self.assertEqual(self.engine.voices(), ['Voice [v]'])
        self.engine.select_voice('Voice [v]')
        self.assertEqual(self.engine.voice, 'v')
        self.request.assert_called_once()

    def test_cache_off_generates_each_time_and_concurrent_hits_generate_once(self):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=2) as pool:
            paths = list(pool.map(lambda _: self.engine.synthesize('same', playback=False), range(2)))
        self.assertEqual(paths[0], paths[1])
        self.request.assert_called_once()
        counter = iter(range(10))
        self.cache.audio_file_path.side_effect = lambda *args: (str(self.root / f'temp{next(counter)}.wav'), False)
        self.engine.synthesize('same', playback=False)
        self.engine.synthesize('same', playback=False)
        self.assertEqual(self.request.call_count, 3)

    def test_fallback_notifies_once_with_reason_and_keeps_preference(self):
        notify, fallback = Mock(), Mock()
        self.response.status_code = 402
        self.response.json.return_value = {'detail': {'status': 'quota_exceeded', 'message': 'secret'}}
        wrapper = FallbackTTS(self.engine, lambda: fallback, Mock(), notify=notify)
        wrapper.initialize()
        wrapper.synthesize('one', playback=False)
        wrapper.synthesize('two', playback=False)
        notify.assert_called_once_with('ElevenLabs', 'ElevenLabs credits exhausted (HTTP 402)')
        self.assertEqual(self.engine.voice, 'voice1')
        self.assertNotIn('secret', wrapper.failure_reason)

    def test_runtime_fallback_notifies_after_successful_startup(self):
        notify = Mock()
        wrapper = FallbackTTS(self.engine, Mock(return_value=Mock()), Mock(), notify=notify)
        wrapper.initialize()
        notify.assert_not_called()
        self.response.status_code = 402
        self.response.json.return_value = {'detail': {'code': 'paid_plan_required', 'status': 'payment_required'}}
        wrapper.synthesize('text', playback=False)
        notify.assert_called_once_with('ElevenLabs', 'This ElevenLabs voice or model requires a paid plan (HTTP 402)')

    def test_detail_code_distinguishes_quota_from_paid_voice_restriction(self):
        self.response.status_code = 402
        for code, expected in (
            ('paid_plan_required', 'This ElevenLabs voice or model requires a paid plan'),
            ('quota_exceeded', 'ElevenLabs credits exhausted'),
        ):
            with self.subTest(code=code):
                self.response.json.return_value = {
                    'detail': {'code': code, 'status': 'payment_required'},
                }
                with self.assertRaisesRegex(AgentError, expected):
                    self.engine.probe()

    def test_voice_selection_can_recover_primary_after_startup_fallback(self):
        primary, fallback = Mock(), Mock()
        primary.provider_name = 'ElevenLabs'
        primary.probe.side_effect = [AgentError('paid plan required'), None]
        wrapper = FallbackTTS(primary, lambda: fallback, Mock())
        wrapper.initialize()
        self.assertIs(wrapper.voice_engine, primary)
        self.assertEqual(wrapper.voices(), primary.voices.return_value)
        fallback.voices.assert_not_called()
        wrapper.select_voice('premade')
        primary.select_voice.assert_called_once_with('premade')
        fallback.select_voice.assert_not_called()
        self.assertEqual(wrapper.provider_name, 'ElevenLabs')
        self.assertIsNone(wrapper.failure_reason)
        wrapper.synthesize('new', playback=False)
        primary.synthesize.assert_called_once()
        fallback.synthesize.assert_not_called()

    def test_failed_voice_retry_keeps_fallback_and_reports_failure(self):
        primary, fallback, notify = Mock(), Mock(), Mock()
        primary.probe.side_effect = AgentError('quota exhausted')
        wrapper = FallbackTTS(primary, lambda: fallback, Mock(), notify)
        wrapper.initialize()
        with self.assertRaisesRegex(AgentError, 'quota exhausted'):
            wrapper.select_voice('premade')
        self.assertEqual(wrapper.provider_name, 'Ollama (fallback)')
        self.assertEqual(notify.call_count, 2)

    def test_rejected_voice_selection_restores_saved_voice(self):
        self.response.json.return_value = {
            'voices': [{'name': 'Original', 'voice_id': 'voice1'},
                       {'name': 'Paid', 'voice_id': 'paid'}], 'has_more': False,
        }
        self.engine.voices()
        self.response.status_code = 402
        self.response.json.return_value = {'detail': {'code': 'paid_plan_required'}}
        wrapper = FallbackTTS(self.engine, Mock(return_value=Mock()), Mock())
        with self.assertRaises(AgentError):
            wrapper.select_voice('paid')
        self.assertEqual(self.values['askai.elevenlabs.tts.voice'], 'voice1')
        self.assertEqual(wrapper.provider_name, 'Ollama (fallback)')

    def test_catalog_collects_pages_sorts_and_refreshes_without_changing_index_snapshot(self):
        self.response.json.side_effect = [
            {'voices': [{'name': 'Zoe', 'voice_id': 'z'}], 'has_more': True, 'next_page_token': 'next'},
            {'voices': [{'name': 'alice', 'voice_id': 'a'}], 'has_more': False},
            {'voices': [{'name': 'Bella', 'voice_id': 'b'}], 'has_more': False},
        ]
        self.assertEqual(self.engine.voices(), ['alice [a]', 'Zoe [z]'])
        self.assertEqual(self.request.call_args.kwargs['params']['next_page_token'], 'next')
        self.assertEqual(self.engine.voices(), ['alice [a]', 'Zoe [z]'])
        self.assertEqual(self.request.call_count, 2)
        self.assertEqual(self.engine.refresh_voices(), ['Bella [b]'])

    def test_live_speech_uses_stream_endpoint_and_publishes_only_complete_audio(self):
        from threading import Event
        self.response.iter_content.return_value = iter([b'\x00\x01', b'\x02\x03'])
        with patch('askai.core.speech.pcm_stream.play_pcm_chunks', return_value=b'\x00\x01\x02\x03') as play:
            path = self.engine.speak_live('[curious]initial comment', Event(), 1)
        self.assertEqual(self.request.call_args.kwargs['json'],
                         {'text': '[curious]initial comment', 'model_id': 'eleven_v4'})
        self.assertTrue(self.request.call_args.kwargs['stream'])
        self.assertTrue(self.request.call_args.args[1].endswith('/stream'))
        play.assert_called_once()
        with wave.open(str(path)) as wav:
            self.assertEqual(wav.readframes(2), b'\x00\x01\x02\x03')
        self.request.reset_mock()
        with patch('askai.core.speech.playback.play_speech') as play_cached:
            self.engine.speak_live('[curious]initial comment', Event(), 1)
            play_cached.assert_called_once()
        self.request.assert_not_called()

    def test_interrupted_stream_does_not_publish_cache(self):
        from threading import Event
        from askai.core.speech.pcm_stream import StartedSpeechError
        with patch('askai.core.speech.pcm_stream.play_pcm_chunks', side_effect=StartedSpeechError('partial')):
            with self.assertRaises(StartedSpeechError):
                self.engine.speak_live('initial', Event(), 1)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_live_playback_error_does_not_switch_provider(self):
        from threading import Event
        from askai.core.speech.pcm_stream import StartedSpeechError
        primary, factory, notify = Mock(), Mock(), Mock()
        primary.provider_name = 'ElevenLabs'
        primary.speak_live.side_effect = StartedSpeechError('player failed')
        wrapper = FallbackTTS(primary, factory, Mock(), notify)
        with self.assertRaises(StartedSpeechError):
            wrapper.speak_live('comment', Event(), 1)
        factory.assert_not_called()
        notify.assert_not_called()
        self.assertEqual(wrapper.provider_name, 'ElevenLabs')

    def test_startup_loads_name_for_previously_selected_voice(self):
        self.engine._generate = Mock()
        self.response.json.return_value = {
            'voices': [{'name': 'Friendly Voice', 'voice_id': 'voice1'}], 'has_more': False,
        }
        self.engine.probe()
        self.assertEqual(self.engine.voice_name, 'Friendly Voice')
        self.assertEqual(self.engine.voice, 'voice1')
        self.assertEqual(self.request.call_args.args[:2],
                         ('GET', 'https://api.elevenlabs.io/v2/voices'))
        self.request.reset_mock()
        self.assertEqual(self.engine.voice_name, 'Friendly Voice')
        self.request.assert_not_called()

    def test_catalogue_failure_does_not_fail_successful_speech_probe(self):
        self.engine._generate = Mock()
        self.engine.voices = Mock(side_effect=AgentError('catalogue unavailable'))
        self.engine.probe()
        self.engine._generate.assert_called_once()
        self.assertEqual(self.engine.voice, 'voice1')

    def test_timestamps_are_cached_with_audio_without_a_second_synthesis(self):
        from askai.core.speech.timing import read_alignment
        alignment = {'characters': list('Hi'), 'character_end_times_seconds': [.01, .02]}
        self.response.json.return_value = {
            'audio_base64': base64.b64encode(self.response.content).decode(), 'alignment': alignment,
        }
        path = self.engine.synthesize('Hi', playback=False)
        self.assertEqual(read_alignment(path), alignment)
        self.assertTrue(self.request.call_args.args[1].endswith('/with-timestamps'))
        self.request.reset_mock()
        self.engine.synthesize('Hi', playback=False)
        self.request.assert_not_called()
