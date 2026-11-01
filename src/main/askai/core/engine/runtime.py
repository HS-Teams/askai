"""Apply explicit engine/model selections between application turns."""
from functools import wraps
from threading import RLock

from askai.core.agents.contracts import AgentError
from askai.core.support.communication import communication


ENGINES = ('codex', 'openai')
_turn_lock = RLock()


def between_turns(function):
    @wraps(function)
    def serialized(*args, **kwargs):
        with _turn_lock:
            return function(*args, **kwargs)
    return serialized


class RuntimeEngines:
    def __init__(self, shared, configs, factory, taius):
        self.shared, self.configs, self.factory, self.taius = shared, configs, factory, taius
        self._engines = {}

    def state(self):
        return {'engine': self.configs.engine, 'model': self.shared.engine.ai_model_name()}

    def engines(self):
        return {**self.state(), 'engines': list(ENGINES)}

    def models(self):
        if self.configs.engine == 'codex':
            models = self.shared.engine.backend.models()
        else:
            models = [{'id': model.model_name(), 'name': model.model_name()}
                      for model in self.shared.engine.models()]
        return {**self.state(), 'models': models}

    @between_turns
    def set_engine(self, name):
        name = name.strip().casefold()
        if name not in ENGINES:
            raise AgentError('Available engines: ' + ', '.join(ENGINES))
        if name != 'codex' and self.shared.mode.processor is self.taius:
            raise AgentError('OpenAI supports Chat/RAG. Select /mode chat or /mode rag before switching.')
        before = self.state()
        if name == self.configs.engine:
            return {**before, 'changed': False}
        self._engines.setdefault(self.configs.engine, self.shared.engine)
        candidate = self._engines.get(name)
        if candidate is None:
            candidate = self.factory.build_engine(name, self.configs.model_for(name))
            if name == 'codex':
                candidate.backend.prepare()
        limit = candidate.ai_token_limit()
        old_engine, old_agent = self.configs.engine, self.configs.agent
        try:
            self.configs.engine = name
            self.configs.agent = name
        except Exception:
            self.configs.engine, self.configs.agent = old_engine, old_agent
            raise
        self.shared.replace_engine(candidate, limit)
        self._engines[name] = candidate
        return self._changed(before)

    @between_turns
    def set_model(self, name):
        name = name.strip()
        if name not in {model['id'] for model in self.models()['models']}:
            raise AgentError('Unknown model for the active engine; use /model list')
        before = self.state()
        if name == before['model']:
            return {**before, 'changed': False}
        engine = self.shared.engine
        old_saved = self.configs.model
        if self.configs.engine == 'codex':
            old_model = engine.model
            limit = engine.backend.context_window(name)
            self.taius.set_model(name)
            try:
                self.configs.model = name
            except Exception:
                self.taius.set_model(old_model)
                self.configs.model = old_saved or ''
                raise
            engine.model = name
            self.shared.context.update_token_limit(limit)
        else:
            candidate = self.factory.build_engine(self.configs.engine, name)
            limit = candidate.ai_token_limit()
            try:
                self.configs.model = name
            except Exception:
                self.configs.model = old_saved or ''
                raise
            self.shared.replace_engine(candidate, limit)
            self._engines[self.configs.engine] = candidate
        return self._changed(before)

    def _changed(self, before):
        result = {**self.state(), 'changed': True, 'previous': before, 'context_preserved': True}
        communication.publish('runtime.selection', result)
        return result


_runtime = None


def runtime_engines():
    global _runtime
    if _runtime is None:
        from askai.core.askai_configs import configs
        from askai.core.engine.engine_factory import EngineFactory
        from askai.core.processors.taius import taius
        from askai.core.support.shared_instances import shared
        _runtime = RuntimeEngines(shared, configs, EngineFactory, taius)
    return _runtime


def response_cache_key(question):
    from askai.core.askai_configs import configs
    from askai.core.support.shared_instances import shared
    return f'{configs.engine}:{shared.engine.ai_model_name()}:{shared.mode.name}:{question}'
