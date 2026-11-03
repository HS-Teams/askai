from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from fixtures.messages import isolated_messages
from askai.language.language import Language


class MessageLanguageCacheTests(unittest.TestCase):
    def setUp(self):
        self.messages = self.enterContext(isolated_messages())

    def test_language_change_does_not_reuse_previous_translation(self):
        self.messages.AskAiMessages._get_translator.cache_clear()
        self.messages.msg._translate.cache_clear()
        self.addCleanup(self.messages.AskAiMessages._get_translator.cache_clear)
        self.addCleanup(self.messages.msg._translate.cache_clear)
        settings = SimpleNamespace(language=Language.EN_US)

        def factory(source, target):
            return Mock(translate=lambda text: target.idiom + ": " + text)

        with patch.object(self.messages, "configs", settings), patch.object(
            self.messages.AskAiMessages, "TRANSLATOR", side_effect=factory
        ) as translator, patch.object(self.messages, "detect_language", return_value="en"):
            self.assertEqual(self.messages.msg.translate("Allow?"), "Allow?")
            settings.language = Language.PT_BR
            self.assertEqual(self.messages.msg.translate("Allow?"), "pt_BR: Allow?")
            self.assertEqual(self.messages.msg.translate("Allow?"), "pt_BR: Allow?")
            self.assertEqual(translator.call_count, 1)
