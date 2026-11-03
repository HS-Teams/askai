import unittest
from io import StringIO
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
        with patch.object(prompt_input.PromptInput, 'cursor', new_callable=lambda: property(lambda self: cursor)), patch.object(
                prompt_input.commons, 'console_out') as console:
            cursor = Mock()
            cursor.position = (1, 14)
            editor.render = Mock()
            editor.flush_messages()
        action.assert_called_once()
        editor.write.assert_not_called()
        self.assertEqual(str(console.control.call_args.args[0]), '\x1b[1G')
        cursor.erase.assert_called_once_with(prompt_input.Direction.DOWN)
        self.assertEqual(cursor.position, (1, 0))
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

    def test_system_notices_clear_real_prompt_and_preserve_draft_and_cursor(self):
        from types import SimpleNamespace
        from clitt.core.term.cursor import Cursor
        from clitt.core.term.terminal import Terminal
        from rich.console import Console
        from rich.text import Text

        for draft, position in (('', 0), ('/gestures', 9), ('mensagem incompleta', 4)):
            with self.subTest(draft=draft):
                output = StringIO()
                console = Console(file=output, force_terminal=True, color_system=None, width=100)
                cursor = object.__new__(Cursor)
                cursor._position = cursor._bottom = (1, 0)
                with patch.object(prompt_input.KeyboardInput, '_HISTORY', ['']), patch.object(
                        prompt_input.sys, 'stdout', output), patch(
                        'hspylib.core.tools.commons.console_out', console), patch.object(Terminal, 'set_show_cursor'):
                    editor = prompt_input.PromptInput('  Hjunior: ', 'Mensagem')
                    editor._terminal = SimpleNamespace(screen=SimpleNamespace(cursor=cursor), echo=cursor.write)
                    editor.text = draft
                    editor._input_index = position
                    editor.render()
                    # The physical prompt must be erased even if its stored column is stale.
                    editor._offset = (0, 0)
                    with patch.object(prompt_input, '_active', editor):
                        prompt_input.present(lambda: console.print(Text('  Sistema: Primeiro aviso')))
                        prompt_input.present(lambda: console.print(Text('  Sistema: Segundo aviso')))
                    editor.flush_messages()
                    self.assertEqual(editor.text, draft)
                    self.assertEqual(editor._input_index, position)
                    self.assertEqual(cursor.position[1], len('  Hjunior: ') + position)
                    self.assertTrue(editor.messages.empty())
                chunks = output.getvalue().split('\x1b[1G\x1b[J')
                self.assertEqual(len(chunks), 3)
                self.assertTrue(chunks[1].startswith('  Sistema: Primeiro aviso\n'))
                self.assertTrue(chunks[2].startswith('  Sistema: Segundo aviso\n'))
                self.assertIn('  Hjunior: ', chunks[1])
                self.assertIn('  Hjunior: ', chunks[2])

    def test_prompt_is_restored_when_notice_rendering_fails(self):
        editor = prompt_input.PromptInput.__new__(prompt_input.PromptInput)
        editor.messages = Queue()
        editor.messages.put(Mock(side_effect=RuntimeError('Cannot render')))
        editor._offset = (0, 10)
        editor.render = Mock()
        cursor = Mock(position=(1, 10))
        with patch.object(prompt_input.PromptInput, 'cursor', property(lambda self: cursor)), patch.object(
                prompt_input.sys, 'stdout', StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'Cannot render'):
                editor.flush_messages()
        editor.render.assert_called_once()
        self.assertEqual(editor._offset, (0, 0))
        self.assertEqual(cursor.position, (1, 0))

    def test_notice_clears_prompt_when_rich_redirects_stdout(self):
        from types import SimpleNamespace
        from clitt.core.term.cursor import Cursor
        from clitt.core.term.terminal import Terminal
        from rich.console import Console
        from rich.file_proxy import FileProxy
        from rich.text import Text

        output = StringIO()
        console = Console(file=output, force_terminal=True, color_system=None, width=100)
        redirected = FileProxy(console, output)
        cursor = object.__new__(Cursor)
        cursor._position = cursor._bottom = (1, 0)
        with patch.object(prompt_input.KeyboardInput, '_HISTORY', ['']), patch.object(
                prompt_input.sys, 'stdout', redirected), patch(
                'hspylib.core.tools.commons.console_out', console), patch.object(Terminal, 'set_show_cursor'):
            editor = prompt_input.PromptInput('  Hjunior: ', 'Mensagem')
            editor._terminal = SimpleNamespace(screen=SimpleNamespace(cursor=cursor), echo=cursor.write)
            editor.text = '/gestures'
            editor._input_index = 4
            editor.render()
            output.seek(0)
            output.truncate()
            with patch.object(prompt_input, '_active', editor):
                prompt_input.present_notice(console, Text('  Sistema: O controle por gestos foi interrompido.'))
            editor.flush_messages()
            self.assertEqual(editor.text, '/gestures')
            self.assertEqual(editor._input_index, 4)
            self.assertEqual(cursor.position[1], len('  Hjunior: ') + 4)

        rendered = output.getvalue()
        self.assertTrue(rendered.startswith('\x1b[1G\x1b[J  Sistema: '), repr(rendered))
        self.assertEqual(rendered.count('  Hjunior: '), 1)
        self.assertIn('interrompido.\n', rendered)

    def test_prepared_notice_serializes_printing_with_prompt_activation(self):
        from threading import Thread
        console = Mock()
        acquired = []

        def try_prompt_lock():
            locked = prompt_input._lock.acquire(blocking=False)
            acquired.append(locked)
            if locked:
                prompt_input._lock.release()

        def print_notice(_):
            thread = Thread(target=try_prompt_lock)
            thread.start()
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive())

        console.print.side_effect = print_notice
        with patch.object(prompt_input, '_active', None):
            prompt_input.present_notice(console, 'Sistema: aviso')
        self.assertEqual(acquired, [False])
        console.print.assert_called_once_with('Sistema: aviso')
