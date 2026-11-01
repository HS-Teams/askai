import unittest
from unittest.mock import Mock
from askai.core.support.usage import Usage, codex_usage, deepl_usage, elevenlabs_usage, read_usage
from askai.core.speech.fallback_tts import FallbackTTS
from askai.core.speech.elevenlabs_tts import ElevenLabsTTS
from askai.core.engine.llama.llama_speech import LlamaSpeech


class UsageTests(unittest.TestCase):
    def test_codex_all_windows_and_buckets_without_assuming_fixed_duration(self):
        data = {'rateLimitsByLimitId': {
            'codex': {'primary': {'usedPercent': 25, 'windowDurationMins': 300, 'resetsAt': 123},
                      'secondary': {'usedPercent': 100, 'windowDurationMins': 10080}},
            'other': {'primary': {'usedPercent': 10, 'windowDurationMins': 60}},
        }, 'rateLimits': {'primary': {'usedPercent': 99}}}
        rows = codex_usage(data)
        self.assertEqual([r.remaining for r in rows], ['75%', '0%', '90%'])
        self.assertEqual(rows[0].window, '300 min')
        self.assertEqual(rows[0].resets_at, 123)

    def test_codex_single_bucket_and_missing_quota(self):
        self.assertEqual(codex_usage({'rateLimits': {'primary': {'usedPercent': 30}}})[0].remaining, '70%')
        for payload in ({}, {'rateLimits': {'primary': {'usedPercent': None}}}):
            with self.assertRaises(ValueError):
                codex_usage(payload)

    def test_elevenlabs_included_free_plan_still_has_real_character_quota(self):
        rows = elevenlabs_usage({'tier': 'free', 'character_count': 44, 'character_limit': 10000})
        self.assertEqual(rows[0].remaining, '99.56%')
        self.assertEqual(rows[0].window, 'characters')

    def test_local_free_is_dash_without_connecting_to_ollama(self):
        client = Mock()
        self.assertEqual(LlamaSpeech(client, Mock()).usage(), [Usage('Ollama', '-')])
        self.assertFalse(client.mock_calls)

    def test_usage_never_initializes_or_probes_speech(self):
        primary, factory = Mock(), Mock()
        wrapper = FallbackTTS(primary, factory, Mock())
        self.assertEqual(wrapper.usage(), primary.usage.return_value)
        primary.probe.assert_not_called()
        primary.synthesize.assert_not_called()
        factory.assert_not_called()
        engine = ElevenLabsTTS(None, None, None)
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.json.return_value = {'character_count': 5, 'character_limit': 10}
        engine._call = Mock(return_value=response)
        self.assertEqual(engine.usage()[0].remaining, '50.00%')
        engine._call.assert_called_once_with('GET', '/v1/user/subscription')

    def test_character_quotas_show_remaining_percentages(self):
        self.assertEqual(elevenlabs_usage({'character_count': 2488, 'character_limit': 39355})[0].remaining, '93.68%')
        self.assertEqual(deepl_usage(Mock(valid=True, count=22918, limit=500000))[0].remaining, '95.42%')
        for used, expected in ((0, '100.00%'), (100, '0.00%'), (120, '0.00%')):
            with self.subTest(used=used):
                self.assertEqual(deepl_usage(Mock(valid=True, count=used, limit=100))[0].remaining, expected)

    def test_nonpositive_character_limits_are_unavailable(self):
        for limit in (0, -1):
            with self.subTest(limit=limit):
                row = read_usage('DeepL', lambda: deepl_usage(Mock(valid=True, count=0, limit=limit)))[0]
                self.assertIsNotNone(row.error)

    def test_errors_are_unavailable_not_zero_or_free(self):
        rows = read_usage('Codex', Mock(side_effect=RuntimeError('offline')))
        self.assertEqual(rows[0].error, 'offline')
        self.assertNotIn(rows[0].remaining, ('0', '-'))

    def test_engine_without_quota_does_not_look_free_or_raise(self):
        from types import SimpleNamespace
        from askai.core.support.usage import engine_usage
        row = engine_usage('openai', SimpleNamespace())[0]
        self.assertTrue(row.error)
        self.assertNotEqual(row.remaining, '-')

    def test_engine_quota_dispatches_to_backend(self):
        from types import SimpleNamespace
        from askai.core.support.usage import engine_usage
        reader = Mock(return_value=[Usage('Codex', '50%')])
        rows = engine_usage('codex', SimpleNamespace(backend=SimpleNamespace(usage=reader)))
        self.assertEqual(rows[0].remaining, '50%')
        reader.assert_called_once_with()
