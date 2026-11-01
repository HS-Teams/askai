import unittest
from types import SimpleNamespace
from askai.core.agents.codex import CodexBackend
from askai.core.support.context_usage import context_label


class ContextUsageTests(unittest.TestCase):
    def test_last_usage_not_cumulative_and_auxiliary_sessions_are_ignored(self):
        backend = CodexBackend()
        backend._context_session = 'main'
        payload = {'last': {'totalTokens': 42000}, 'total': {'totalTokens': 990000},
                   'modelContextWindow': 128000}
        backend._update_context_usage('main', payload)
        self.assertEqual(backend.context_usage(), {'used': 42000, 'limit': 128000})
        backend._update_context_usage('aux', {**payload, 'last': {'totalTokens': 100}})
        self.assertEqual(backend.context_usage()['used'], 42000)
        self.assertEqual(context_label(SimpleNamespace(backend=backend), lambda s: s),
                         'Context: 42K / 128K · 33% used · 86K free')

    def test_unknown_data_and_private_reset(self):
        backend = CodexBackend()
        self.assertIn('Awaiting data', context_label(SimpleNamespace(backend=backend), lambda s: s))
        backend._context_session = 'private'
        backend._private_sessions.add('private')
        backend._context_usage = {'used': 10, 'limit': 100}
        backend.archive('private')
        self.assertIsNone(backend.context_usage())

    def test_invalid_window_does_not_produce_a_percentage(self):
        backend = CodexBackend()
        backend._context_session = 'main'
        for limit in (None, 0, -1, True):
            backend._update_context_usage('main', {'last': {'totalTokens': 10}, 'modelContextWindow': limit})
            self.assertIsNone(backend.context_usage())
