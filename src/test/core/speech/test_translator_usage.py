import unittest
from unittest.mock import Mock
import deepl
from askai.language.translators.deepl_translator import DeepLTranslator
from askai.language.ai_translator import AITranslator
from askai.core.support.usage import read_usage


class TranslatorUsageTests(unittest.TestCase):
    def test_free_quota_is_reported_without_translating(self):
        translator = DeepLTranslator(None, None)
        client = translator._translator = Mock()
        client.get_usage.return_value = deepl.Usage({'character_count': 28, 'character_limit': 500000})
        row = translator.usage()[0]
        self.assertEqual(row.remaining, '99.99%')
        self.assertEqual(row.window, 'characters')
        self.assertIsNone(row.resets_at)
        client.translate_text.assert_not_called()

    def test_api_failure_and_missing_quota_are_not_free(self):
        translator = DeepLTranslator(None, None)
        translator._translator = Mock()
        translator._translator.get_usage.side_effect = deepl.DeepLException('unavailable')
        self.assertTrue(read_usage('DeepL', translator.usage)[0].error)
        translator._translator.get_usage.side_effect = None
        translator._translator.get_usage.return_value = deepl.Usage({})
        self.assertTrue(read_usage('DeepL', translator.usage)[0].error)

    def test_local_translator_shows_dash(self):
        translator = AITranslator(None, None)
        translator.name = lambda: 'Local'
        self.assertEqual(translator.usage()[0].remaining, '-')
