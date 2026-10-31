import unittest
from unittest.mock import Mock, patch
from pydantic import ValidationError
from askai.core.model.refined_response import RefinedResponse
from askai.core.speech.narration import parse_narration, translate_narration


class NarrationTests(unittest.TestCase):
    def test_delivery_cues_are_spoken_but_hidden_in_both_visual_views(self):
        from askai.core.speech.presentation import format_narration
        narration = parse_narration('Source [happy]\n<TTS>[happy]Hello [curious]there.</TTS>')
        self.assertEqual(narration.spoken, '[happy]Hello [curious]there.')
        self.assertEqual(narration.visible, 'Source [happy]\nHello there.')
        self.assertEqual(format_narration(narration), 'Source [happy]\n降 Hello there.')

    def test_translation_preserves_cues_and_spacing(self):
        translator = Mock(side_effect=lambda text: text.upper())
        translated = translate_narration('<TTS>[happy] Hello [whispers] there.</TTS>', translator)
        self.assertEqual(translated, '<TTS>[happy] HELLO [whispers] THERE.</TTS>')
        self.assertEqual([call.args[0] for call in translator.call_args_list], ['Hello', 'there.'])

    def test_delivery_cues_alone_are_not_valid_narration(self):
        with self.assertRaises(ValidationError):
            RefinedResponse(final_answer='<TTS>[happy] [laughs]</TTS>')

    def test_bracketed_content_is_not_removed_as_a_delivery_cue(self):
        narration = parse_narration('<TTS>Use [filename] and [1].</TTS>')
        self.assertEqual(narration.visible, 'Use [filename] and [1].')

    def test_cli_progressive_display_hides_delivery_cues(self):
        from threading import Event
        from askai.cli.speech_renderer import stream_answer
        console = Mock(is_terminal=True)
        narration = parse_narration('Sources\n<TTS>[happy]Hello.</TTS>')
        with patch('askai.cli.speech_renderer.Live'), \
             patch('askai.cli.speech_renderer.render_answer'), \
             patch('askai.cli.speech_renderer.reveal_text') as reveal:
            stream_answer(console, narration.visible, 'Taius', 1, Event(), narration)
        self.assertEqual(reveal.call_args.args[0], 'Hello.')
        self.assertNotIn('[happy]', str(console.print.call_args_list))

    def test_only_marked_text_is_spoken_but_all_content_stays_visible(self):
        text = 'Fontes: Climatempo\n\nHjunior, <TTS>há previsão de chuva.</TTS>'
        result = parse_narration(text, required=True)
        self.assertEqual(result.spoken, 'há previsão de chuva.')
        self.assertEqual(result.visible, 'Fontes: Climatempo\n\nHjunior, há previsão de chuva.')
        self.assertEqual(RefinedResponse(final_answer=text).final_answer, text)

    def test_missing_or_malformed_markup_cannot_pass_refiner_validation(self):
        for text in ('<TTS>Hello</TTS>later content', 'hello', '<TTS></TTS>', '<TTS> </TTS>', '<TTS>open',
                     '</TTS>closed<TTS>', '<tts>case</tts>', '<TTS a="b">hi</TTS>',
                     '<TTS>one</TTS><TTS>two</TTS>', '<TTS>one<TTS>two</TTS></TTS>'):
            with self.subTest(text=text), self.assertRaises(ValidationError):
                RefinedResponse(final_answer=text)

    def test_unmarked_old_response_is_visible_but_never_narrated(self):
        result = parse_narration('Old cached response with URLs and logs')
        self.assertEqual(result.visible, 'Old cached response with URLs and logs')
        self.assertEqual(result.spoken, '')

    def test_translation_does_not_receive_or_change_delimiters(self):
        translator = Mock(side_effect=lambda text: text.upper())
        translated = translate_narration('before <TTS>hello</TTS> after', translator)
        self.assertEqual(translated, 'BEFORE <TTS>HELLO</TTS> AFTER')
        self.assertTrue(all('<TTS>' not in call.args[0] for call in translator.call_args_list))
        self.assertEqual(parse_narration(translated).spoken, 'HELLO')
