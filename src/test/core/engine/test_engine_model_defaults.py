"""Per-engine preferences must never reuse another provider's model."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

from hspylib.core.metaclass.singleton import Singleton


class TestEngineModelDefaults(unittest.TestCase):
    def setUp(self):
        self.values = {"askai.default.engine": "openai", "askai.default.engine.model": "gpt-4o-mini"}
        settings_module = ModuleType("askai.core.askai_settings")
        settings_module.settings = SimpleNamespace(
            get=lambda key: self.values.get(key, ""),
            put=self.values.__setitem__, get_list=lambda key: [],
        )
        classpath_module = ModuleType("askai.__classpath__")
        classpath_module.classpath = SimpleNamespace(resource_path=Path("."))
        modules = patch.dict(sys.modules, {
            "askai.core.askai_settings": settings_module,
            "askai.__classpath__": classpath_module,
        })
        modules.start()
        self.addCleanup(modules.stop)
        singletons = patch.dict(Singleton._instances, clear=True)
        singletons.start()
        self.addCleanup(singletons.stop)
        sys.modules.pop("askai.core.askai_configs", None)
        self.configs = importlib.import_module("askai.core.askai_configs").configs

    def test_global_model_is_not_used_as_codex_default(self):
        self.assertIsNone(self.configs.model_for("codex"))
        self.assertIsNone(self.configs.model_for("openai"))

    def test_switching_engines_preserves_both_models(self):
        self.configs.model = "gpt-4.1"
        self.configs.engine = "codex"
        self.assertIsNone(self.configs.model)
        self.configs.model = "agent-model"
        self.configs.engine = "openai"
        self.assertEqual(self.configs.model, "gpt-4.1")
        self.assertEqual(self.configs.model_for("codex"), "agent-model")
        self.assertEqual(self.values["askai.default.engine.model"], "gpt-4o-mini")

    def test_empty_preferences_allow_factory_default(self):
        for value in ["", "   "]:
            self.values["askai.codex.default.model"] = value
            self.assertIsNone(self.configs.model_for("codex"))

    def test_future_engine_has_independent_preference(self):
        self.configs.engine = "another-provider"
        self.configs.model = "custom-model"
        self.assertEqual(self.configs.model_for("another-provider"), "custom-model")
        self.assertIsNone(self.configs.model_for("codex"))


if __name__ == "__main__":
    unittest.main()
