import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from askai.core.askai_messages import AskAiMessages, msg
from askai.language.ai_translator import AITranslator
from askai.language.language import Language
from askai.language.detection import detect_language


class TranslationPolicyTests(unittest.TestCase):
    def setUp(self):
        msg._translate.cache_clear()
        AskAiMessages._get_translator.cache_clear()
        self.addCleanup(msg._translate.cache_clear)
        self.addCleanup(AskAiMessages._get_translator.cache_clear)

    def test_same_language_technical_message_never_constructs_provider(self):
        text = 'A captura foi concluída com sucesso.'
        with patch('askai.core.askai_messages.configs', SimpleNamespace(language=Language.PT_BR)), patch.object(AskAiMessages, 'TRANSLATOR') as factory:
            self.assertEqual(msg.translate(text), text)
            factory.assert_not_called()

    def test_response_follows_question_instead_of_ui_language(self):
        provider = Mock()
        provider.translate.return_value = 'translated'
        with patch('askai.core.askai_messages.configs', SimpleNamespace(language=Language.PT_BR)), patch.object(AskAiMessages, 'TRANSLATOR', return_value=provider) as factory:
            question = 'Please describe what you can see in this photograph.'
            answer = 'The photograph shows a table and a chair.'
            self.assertEqual(msg.translate_response(answer, question), answer)
            factory.assert_not_called()
            self.assertEqual(msg.translate_response('A fotografia mostra uma mesa e uma cadeira.', question), 'translated')
            source, target = factory.call_args.args
            self.assertEqual((source.language, target.language), ('pt', 'en'))
            provider.translate.assert_called_once()

    def test_unknown_or_code_only_text_never_calls_provider(self):
        with patch.object(AskAiMessages, 'TRANSLATOR') as factory:
            for text in ('', '12345', '```python\nprint(123)\n```'):
                self.assertEqual(msg.translate(text), text)
            factory.assert_not_called()

    def test_provider_base_skips_regional_variants_and_already_translated_text(self):
        translator = AITranslator(Language.EN_US, Language.PT_BR)
        translator._translate_text = Mock()
        text = 'A fotografia mostra uma mesa e uma cadeira.'
        self.assertEqual(translator.translate(text), text)
        translator._translate_text.assert_not_called()
        translator = AITranslator(Language.PT_PT, Language.PT_BR)
        translator._translate_text = Mock()
        self.assertEqual(translator.translate(text), text)
        translator._translate_text.assert_not_called()

    def test_provider_preserves_code_links_and_spacing(self):
        translator = AITranslator(Language.EN_US, Language.PT_BR)
        translator._translate_text = Mock(side_effect=lambda value: value.replace('Open this file', 'Abra este arquivo'))
        text = 'Open this file `example.py`.\n\n```python\nprint("Hello")\n```\nhttps://example.com'
        with patch('askai.language.ai_translator.detect_language', return_value='en'):
            translated = translator.translate(text)
        self.assertEqual(translated, text.replace('Open this file', 'Abra este arquivo'))
        for call in translator._translate_text.call_args_list:
            self.assertNotIn('print(', call.args[0])
            self.assertNotIn('https://', call.args[0])

    def test_ambiguous_detection_returns_no_language(self):
        self.assertIsNone(detect_language('12345'))

    def test_foreign_technical_message_is_translated_once_and_cached(self):
        provider = Mock()
        provider.translate.return_value = 'Permitir que o aplicativo acesse a câmera?'
        with patch('askai.core.askai_messages.configs', SimpleNamespace(language=Language.PT_BR)), patch.object(AskAiMessages, 'TRANSLATOR', return_value=provider) as factory:
            text = 'Allow this application to access the camera?'
            self.assertEqual(msg.translate(text), provider.translate.return_value)
            self.assertEqual(msg.translate(text), provider.translate.return_value)
            factory.assert_called_once()
            provider.translate.assert_called_once_with(text)

    def test_unknown_question_does_not_trigger_response_translation(self):
        with patch.object(AskAiMessages, 'TRANSLATOR') as factory:
            text = 'The photograph shows a table and a chair.'
            self.assertEqual(msg.translate_response(text, '12345'), text)
            factory.assert_not_called()


    def test_app_messages_default_to_english_when_detection_is_inconclusive(self):
        provider = Mock()
        provider.translate.return_value = 'Até logo, tenha um bom dia!'
        with patch('askai.core.askai_messages.configs', SimpleNamespace(language=Language.PT_BR)), patch.object(
            AskAiMessages, 'TRANSLATOR', return_value=provider
        ) as factory, patch('askai.core.askai_messages.detect_language', return_value=None):
            self.assertEqual(msg.translate(msg.goodbye()), provider.translate.return_value)
            factory.assert_called_once_with(Language.EN_US, Language.PT_BR)
            provider.translate.assert_called_once_with(msg.goodbye())

    def test_english_ui_does_not_translate_ambiguous_app_messages(self):
        with patch('askai.core.askai_messages.configs', SimpleNamespace(language=Language.EN_US)), patch.object(
            AskAiMessages, 'TRANSLATOR'
        ) as factory, patch('askai.core.askai_messages.detect_language', return_value=None):
            self.assertEqual(msg.translate(msg.goodbye()), msg.goodbye())
            factory.assert_not_called()

    def test_unknown_agent_response_does_not_inherit_app_source(self):
        with patch.object(AskAiMessages, 'TRANSLATOR') as factory, patch(
            'askai.core.askai_messages.detect_language', side_effect=['pt', None]
        ):
            self.assertEqual(msg.translate_response('Ambiguous response', 'Pergunta'), 'Ambiguous response')
            factory.assert_not_called()
