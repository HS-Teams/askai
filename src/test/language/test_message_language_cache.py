from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from askai.core.askai_messages import AskAiMessages, msg
from askai.language.language import Language


class MessageLanguageCacheTests(unittest.TestCase):
    def test_language_change_does_not_reuse_previous_translation(self):
        AskAiMessages._get_translator.cache_clear()
        msg._translate.cache_clear()
        self.addCleanup(AskAiMessages._get_translator.cache_clear)
        self.addCleanup(msg._translate.cache_clear)
        settings = SimpleNamespace(language=Language.EN_US)

        def factory(source, target):
            return Mock(translate=lambda text: target.idiom + ": " + text)

        with patch("askai.core.askai_messages.configs", settings), patch.object(
            AskAiMessages, "TRANSLATOR", side_effect=factory
        ) as translator:
            self.assertEqual(msg.translate("Allow?"), "en_US: Allow?")
            settings.language = Language.PT_BR
            self.assertEqual(msg.translate("Allow?"), "pt_BR: Allow?")
            self.assertEqual(msg.translate("Allow?"), "pt_BR: Allow?")
            self.assertEqual(translator.call_count, 2)
