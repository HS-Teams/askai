import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch


class RuntimeEmbeddingTests(unittest.TestCase):
    def setUp(self):
        self.engine = Mock()
        self.engine.embedding_key.return_value = 'space-a'
        modules = {}
        for name, attrs in {
            'askai.core.askai_configs': {'configs': SimpleNamespace(rag_retrival_amount=3)},
            'askai.core.component.cache_service': {'PERSIST_DIR': Path('/indexes')},
            'askai.core.support.shared_instances': {'shared': SimpleNamespace(engine=self.engine)},
        }.items():
            module = ModuleType(name)
            module.__dict__.update(attrs)
            modules[name] = module
        self.patch = patch.dict('sys.modules', modules)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        path = Path(__file__).parents[3] / 'main/askai/core/component/summarizer.py'
        spec = importlib.util.spec_from_file_location('runtime_summarizer_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.summarizer = module.Summarizer()
        self.summarizer._index = Mock()
        self.summarizer._folder, self.summarizer._glob = '/docs', '*.md'
        self.summarizer._embedding_key = 'space-a'

    def test_embedding_space_change_requires_reopening_collection_before_search(self):
        self.assertTrue(self.summarizer.exists('/docs', '*.md'))
        self.engine.embedding_key.return_value = 'space-b'
        self.assertFalse(self.summarizer.exists('/docs', '*.md'))
        def generate(folder, glob):
            self.summarizer._embedding_key = 'space-b'
        self.summarizer.generate = Mock(side_effect=generate)
        self.summarizer._index.search.return_value = []
        self.summarizer.retrieve('question')
        self.summarizer.generate.assert_called_once_with('/docs', '*.md')

    def test_same_embedding_space_keeps_the_current_collection(self):
        self.summarizer.generate = Mock()
        self.summarizer._index.search.return_value = []
        self.summarizer.retrieve('question')
        self.summarizer.generate.assert_not_called()
