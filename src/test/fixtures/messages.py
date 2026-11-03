"""Load real message logic without application settings or external providers."""

from contextlib import contextmanager
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from hspylib.core.metaclass.singleton import Singleton
from askai.language.language import Language


@contextmanager
def isolated_messages():
    configs = SimpleNamespace(language=Language.EN_US, is_cache=True)
    modules = {
        'askai.core.askai_configs': SimpleNamespace(configs=configs),
        'askai.language.translators.deepl_translator': SimpleNamespace(DeepLTranslator=Mock()),
    }
    path = Path(__file__).parents[2] / 'main/askai/core/askai_messages.py'
    spec = importlib.util.spec_from_file_location('messages_under_test', path)
    module = importlib.util.module_from_spec(spec)
    with patch.dict('sys.modules', modules), patch.dict(Singleton._instances):
        Singleton._instances.pop('AskAiMessages', None)
        spec.loader.exec_module(module)
        yield module
