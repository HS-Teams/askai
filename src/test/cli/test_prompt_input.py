import unittest
from queue import Queue
from unittest.mock import Mock, patch
from askai.cli import prompt_input


class PromptInputTests(unittest.TestCase):
    def test_reply_queued_while_typing_then_prompt_redrawn(self):
        editor = prompt_input.PromptInput.__new__(prompt_input.PromptInput)
        editor.messages = Queue()
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
