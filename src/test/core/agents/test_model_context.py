import json
import tempfile
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

from askai.core.agents.model_context import codex_context_window
from askai.core.agents.codex import CodexBackend
from askai.core.engine.agent.agent_engine import AgentEngine


class ModelContextTests(unittest.TestCase):
    def test_catalogue_uses_selected_model_effective_window_not_maximum(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'CODEX_HOME': folder}):
            path = Path(folder) / 'models_cache.json'
            self.assertIsNone(codex_context_window('selected'))
            path.write_text(json.dumps({'models': [
                {'slug': 'other', 'context_window': 100},
                {'slug': 'selected', 'context_window': 500000, 'max_context_window': 872000,
                 'effective_context_window_percent': 95},
            ]}))
            self.assertEqual(codex_context_window('selected'), 475000)
            self.assertIsNone(codex_context_window('unknown'))
            self.assertIsNone(codex_context_window(None))
            path.write_text('not json')
            self.assertIsNone(codex_context_window('selected'))

    def test_invalid_capacities_are_not_displayed(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'CODEX_HOME': folder}):
            for window in (0, -1, True, '500000', None):
                Path(folder, 'models_cache.json').write_text(json.dumps({'models': [
                    {'slug': 'selected', 'context_window': window}]}))
                self.assertIsNone(codex_context_window('selected'))

    def test_runtime_window_overrides_catalogue_only_for_active_model(self):
        backend = CodexBackend()
        backend._active_model = 'selected'
        transport = Mock()
        transport.receive.side_effect = [
            {'method': 'thread/tokenUsage/updated', 'params': {'threadId': 's', 'tokenUsage': {'modelContextWindow': 123456}}},
            {'method': 'item/completed', 'params': {'item': {'id': 'a', 'type': 'agentMessage', 'phase': 'final_answer', 'text': 'Done'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ]
        backend._consume(transport, 's', 't', Mock(), Mock(), Event())
        with patch('askai.core.agents.codex.codex_context_window', return_value=None):
            self.assertEqual(backend.context_window('selected'), 123456)
            self.assertIsNone(backend.context_window('other'))

    def test_engine_gets_model_capacity_from_backend(self):
        with patch('askai.core.engine.agent.agent_engine.create_backend') as factory:
            factory.return_value.context_window.return_value = 475000
            engine = AgentEngine('codex', 'selected')
            self.assertEqual(engine.ai_token_limit(), 475000)
            factory.return_value.context_window.assert_called_once_with('selected')
