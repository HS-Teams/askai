import unittest
from queue import Queue
from unittest.mock import Mock, patch
from askai.cli import prompt_input


class PromptInputTests(unittest.TestCase):
    def test_typed_slash_prefix_suggests_command_and_tab_completes_it(self):
        for prefix in ('/', '/g', '/ges', '/GES'):
            with self.subTest(prefix=prefix), patch.object(
                    prompt_input.KeyboardInput, '_HISTORY', ['/gestures', '/info', '']), patch.object(
                    prompt_input.PromptInput, 'cursor', property(lambda self: Mock())):
                editor = prompt_input.PromptInput('', '')
                editor.write = Mock()
                editor._update_input(prefix)
                hint = editor._render_suggestions()
                self.assertEqual(hint, '/gestures'[len(prefix):])
                editor.write.assert_called_once_with(f'%GRAY%{hint}%NC%')
                editor.complete()
                self.assertEqual(editor.text.casefold(), '/gestures')

    def test_completed_command_and_unknown_prefix_do_not_suggest_draft(self):
        for prefix in ('/gestures', '/unknown'):
            with self.subTest(prefix=prefix), patch.object(
                    prompt_input.KeyboardInput, '_HISTORY', ['/gestures --help', '/gestures', '']), patch.object(
                    prompt_input.PromptInput, 'cursor', property(lambda self: Mock())):
                editor = prompt_input.PromptInput('', '')
                editor.write = Mock()
                editor._update_input(prefix)
                self.assertEqual(editor._render_suggestions(), '')
                editor.write.assert_not_called()

    def test_command_arguments_and_recall_still_work_in_same_session(self):
        with patch.object(prompt_input.KeyboardInput, '_HISTORY', ['/gestures --help', '/info', '']), patch.object(
                prompt_input.PromptInput, 'cursor', property(lambda self: Mock())):
            editor = prompt_input.PromptInput('', '')
            editor.write = Mock()
            editor._update_input('/gestures ')
            self.assertEqual(editor._render_suggestions(), '--help')
            editor.complete()
            editor._add_history(editor.text)
            next_editor = prompt_input.PromptInput('', '')
            self.assertEqual(next_editor._prev_in_history(), '/gestures --help')

    def test_reply_queued_while_typing_then_prompt_redrawn(self):
        editor = prompt_input.PromptInput.__new__(prompt_input.PromptInput)
        editor.messages = Queue()
        editor.write = Mock()
        editor._offset = (0, 14)
        action = Mock()
        with patch.object(prompt_input, '_active', editor):
            prompt_input.present(action)
        action.assert_not_called()
        with patch.object(prompt_input.PromptInput, 'cursor', new_callable=lambda: property(lambda self: cursor)):
            cursor = Mock()
            editor.render = Mock()
            editor.flush_messages()
        action.assert_called_once()
        editor.write.assert_called_once_with('\r')
        editor.render.assert_called_once()
        self.assertEqual(editor._offset, (0, 0))

    def test_reply_without_active_input_is_immediate(self):
        action = Mock()
        with patch.object(prompt_input, '_active', None):
            prompt_input.present(action)
        action.assert_called_once()

    def test_voice_is_only_requested_for_empty_question_prompt(self):
        from threading import Event
        editor = Mock(allow_voice=True, text='', voice_requested=Event())
        with patch.object(prompt_input, '_active', editor):
            self.assertTrue(prompt_input.request_voice())
            self.assertTrue(editor.voice_requested.is_set())
            editor.text = 'unfinished'
            self.assertFalse(prompt_input.request_voice())
            editor.text = ''
            editor.allow_voice = False
            self.assertFalse(prompt_input.request_voice())
        with patch.object(prompt_input, '_active', None):
            self.assertFalse(prompt_input.request_voice())
