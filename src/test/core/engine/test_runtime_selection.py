from threading import Event, Thread
from contextlib import nullcontext
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from askai.core.agents.contracts import AgentError, AgentTask
from askai.core.agents.codex import CodexBackend
from askai.core.engine.runtime import RuntimeEngines, between_turns, response_cache_key
from askai.core.orchestration.orchestrator import Orchestrator


class Configs:
    def __init__(self):
        self.engine = self.agent = 'codex'
        self.saved = {'codex': 'model-a', 'openai': 'api-model'}
        self.fail_model = False

    @property
    def model(self):
        return self.saved[self.engine]

    @model.setter
    def model(self, value):
        if self.fail_model:
            self.fail_model = False
            raise RuntimeError('Settings unavailable')
        self.saved[self.engine] = value

    def model_for(self, engine):
        return self.saved[engine]


def engine(name, model):
    result = Mock(spec=['model', 'backend', 'ai_model_name', 'ai_token_limit', 'models'])
    result.model = model
    result.ai_model_name.side_effect = lambda: result.model
    result.ai_token_limit.return_value = 8000
    result.backend.models.return_value = [{'id': 'model-a', 'name': 'A'}, {'id': 'model-b', 'name': 'B'}]
    result.backend.context_window.return_value = 16000
    result.models.return_value = [SimpleNamespace(model_name=lambda: 'api-model')]
    return result


class RuntimeSelectionTests(unittest.TestCase):
    def setUp(self):
        self.configs, self.taius = Configs(), Mock()
        self.original = engine('codex', 'model-a')
        self.context = SimpleNamespace(messages=['old user message', 'old answer'], update_token_limit=Mock())
        self.memory, self.speech = object(), object()
        self.shared = SimpleNamespace(engine=self.original, context=self.context,
                                      memory=self.memory, speech=self.speech,
                                      mode=SimpleNamespace(processor=object()))
        def replace(candidate, limit):
            self.shared.engine = candidate
            self.shared.context.update_token_limit(limit)
        self.shared.replace_engine = Mock(side_effect=replace)
        self.factory = Mock()
        self.factory.build_engine.side_effect = engine
        self.runtime = RuntimeEngines(self.shared, self.configs, self.factory, self.taius)
        self.bus = patch('askai.core.engine.runtime.communication')
        self.communication = self.bus.start()
        self.addCleanup(self.bus.stop)

    def test_engine_round_trip_preserves_context_memory_speech_and_native_backend(self):
        self.runtime.set_engine('openai')
        self.assertEqual(self.configs.engine, 'openai')
        self.assertIs(self.shared.context, self.context)
        self.assertIs(self.shared.memory, self.memory)
        self.assertIs(self.shared.speech, self.speech)
        self.assertEqual(self.context.messages, ['old user message', 'old answer'])
        self.runtime.set_engine('codex')
        self.assertIs(self.shared.engine, self.original)
        self.factory.build_engine.assert_called_once_with('openai', 'api-model')
        self.communication.publish.assert_called_with('runtime.selection', {
            'engine': 'codex', 'model': 'model-a', 'changed': True,
            'previous': {'engine': 'openai', 'model': 'api-model'}, 'context_preserved': True})

    def test_codex_model_change_keeps_engine_backend_and_updates_orchestrator(self):
        backend = self.original.backend
        self.runtime.set_model('model-b')
        self.assertIs(self.shared.engine, self.original)
        self.assertIs(self.shared.engine.backend, backend)
        self.assertEqual(self.original.model, 'model-b')
        self.assertEqual(self.configs.saved['codex'], 'model-b')
        self.taius.set_model.assert_called_once_with('model-b')
        self.context.update_token_limit.assert_called_once_with(16000)
        self.factory.build_engine.assert_not_called()

    def test_unknown_engine_or_model_never_changes_active_selection(self):
        for operation, value in [(self.runtime.set_engine, 'claude'), (self.runtime.set_model, 'not-a-model')]:
            with self.subTest(value=value), self.assertRaises(AgentError):
                operation(value)
        self.assertIs(self.shared.engine, self.original)
        self.assertEqual(self.configs.engine, 'codex')
        self.assertEqual(self.original.model, 'model-a')
        self.communication.publish.assert_not_called()

    def test_failed_engine_construction_preserves_active_engine_and_settings(self):
        self.factory.build_engine.side_effect = RuntimeError('Missing API key')
        with self.assertRaisesRegex(RuntimeError, 'Missing API key'):
            self.runtime.set_engine('openai')
        self.assertIs(self.shared.engine, self.original)
        self.assertEqual(self.configs.engine, 'codex')
        self.shared.replace_engine.assert_not_called()

    def test_model_settings_failure_restores_orchestrator_and_keeps_old_model(self):
        self.configs.fail_model = True
        with self.assertRaisesRegex(RuntimeError, 'Settings unavailable'):
            self.runtime.set_model('model-b')
        self.assertEqual(self.original.model, 'model-a')
        self.assertEqual(self.configs.model, 'model-a')
        self.assertEqual([call.args[0] for call in self.taius.set_model.call_args_list], ['model-b', 'model-a'])

    def test_taius_does_not_silently_switch_mode_for_openai(self):
        self.shared.mode.processor = self.taius
        with self.assertRaisesRegex(AgentError, '/mode chat'):
            self.runtime.set_engine('openai')
        self.assertEqual(self.configs.engine, 'codex')
        self.factory.build_engine.assert_not_called()

    def test_engine_and_model_catalogues_identify_active_selection(self):
        self.assertEqual(self.runtime.engines()['engines'], ['codex', 'openai'])
        self.assertEqual(self.runtime.models()['models'][1]['id'], 'model-b')
        self.runtime.set_engine('openai')
        self.assertEqual(self.runtime.models()['models'][0]['id'], 'api-model')

    def test_switch_waits_for_active_application_turn(self):
        entered, release, changed = Event(), Event(), Event()
        @between_turns
        def active_turn():
            entered.set()
            release.wait(timeout=2)
        first = Thread(target=active_turn)
        second = Thread(target=lambda: (self.runtime.set_model('model-b'), changed.set()))
        first.start()
        self.assertTrue(entered.wait(timeout=1))
        second.start()
        try:
            self.assertFalse(changed.wait(timeout=.05))
        finally:
            release.set()
            first.join(timeout=2)
            second.join(timeout=2)
        self.assertTrue(changed.is_set())

    def test_cache_identity_separates_models_engines_and_modes(self):
        configs = ModuleType('askai.core.askai_configs')
        configs.configs = self.configs
        shared = ModuleType('askai.core.support.shared_instances')
        shared.shared = self.shared
        self.shared.mode.name = 'CHAT'
        with patch.dict('sys.modules', {configs.__name__: configs, shared.__name__: shared}):
            first = response_cache_key('hello')
            self.original.model = 'model-b'
            second = response_cache_key('hello')
            self.configs.engine = 'openai'
            third = response_cache_key('hello')
            self.shared.mode.name = 'RAG'
            fourth = response_cache_key('hello')
        self.assertEqual(len({first, second, third, fourth}), 4)


class CodexModelCatalogueTests(unittest.TestCase):
    def test_private_resumed_turn_receives_the_new_model_and_input_budget(self):
        backend, transport = CodexBackend(), Mock()
        backend._private_sessions.add('session')
        backend._active_model = 'model-a'
        backend._connections = Mock()
        backend._connections.lease.return_value = nullcontext(transport)
        transport.request.return_value = {'turn': {'id': 'turn'}}
        with patch.object(backend, '_consume', return_value=Mock()), \
             patch.object(backend, 'context_window', return_value=16000) as context_window, \
             patch('askai.core.agents.codex.prepared_input', return_value=nullcontext('hello')):
            backend.run(AgentTask('hello', Path.cwd(), session_id='session', model='model-b',
                                  persist_history=False), Mock(), Mock(), Event())
        context_window.assert_called_with('model-b')
        self.assertEqual(transport.request.call_args.args[1]['model'], 'model-b')
        self.assertEqual(transport.request.call_args.args[0], 'turn/start')

    def test_catalogue_collects_all_pages_using_model_identifiers(self):
        backend, transport = CodexBackend(), Mock()
        backend._connections = Mock()
        backend._connections.lease.return_value.__enter__ = Mock(return_value=transport)
        backend._connections.lease.return_value.__exit__ = Mock(return_value=False)
        transport.request.side_effect = [
            {'data': [{'model': 'model-a', 'displayName': 'A', 'isDefault': True}], 'nextCursor': 'next'},
            {'data': [{'model': 'model-b', 'displayName': 'B', 'isDefault': False}], 'nextCursor': None}]
        self.assertEqual([model['id'] for model in backend.models()], ['model-a', 'model-b'])
        self.assertEqual(transport.request.call_args.args, ('model/list', {'limit': 100, 'cursor': 'next'}))

    def test_orchestrator_model_update_preserves_native_session_ids(self):
        orchestrator = Orchestrator(Mock(), Mock(), Mock(), Mock(), Mock(), model='model-a')
        orchestrator._sessions[('cwd', 'day')] = 'existing-session'
        orchestrator.set_model('model-b')
        self.assertEqual(orchestrator._sessions[('cwd', 'day')], 'existing-session')
        self.assertEqual(orchestrator._model, 'model-b')
        orchestrator._active.acquire()
        try:
            with self.assertRaises(AgentError):
                orchestrator.set_model('model-a')
            self.assertEqual(orchestrator._model, 'model-b')
        finally:
            orchestrator._active.release()
