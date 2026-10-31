"""Regression: refinement must load its prompt through the real resource reader."""
import importlib
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from hspylib.core.metaclass.singleton import Singleton


class TestRefinerPromptLoading(unittest.TestCase):
    def test_action_loads_nested_prompt_before_invoking_refiner(self):
        resources = Path(__file__).parents[3] / 'main/askai/resources'
        formatter = Mock()
        formatter.strip_format.side_effect = lambda value: value
        formatter.escape_markdown.side_effect = lambda value: value
        services = {
            'askai.__classpath__': {'classpath': SimpleNamespace(resource_path=resources)},
        }
        modules = {}
        for name, attributes in services.items():
            modules[name] = ModuleType(name)
            modules[name].__dict__.update(attributes)
        with patch.dict(sys.modules, modules), patch.dict(Singleton._instances, clear=True):
            for name in ['askai.core.askai_prompt', 'askai.core.support.utilities']:
                sys.modules.pop(name, None)
            prompt = importlib.import_module('askai.core.askai_prompt').prompt
            template = prompt.read_prompt('taius-refiner.txt', prompt.append_path('taius'))
            self.assertEqual(template, (resources / 'prompts/taius/taius-refiner.txt').read_text())
            self.assertIn('Output Contract', template)
