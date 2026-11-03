"""Test the real Click registry without loading devices or personal stores."""
import ast
from pathlib import Path
from string import Template
from textwrap import dedent
import unittest
from unittest.mock import Mock, call, patch
import click
from click.testing import CliRunner
from askai.cli.help_formatter import HelpGroup
from askai.cli.gestures_help import GesturesCommand


class CommandHelpTests(unittest.TestCase):
    def test_runtime_commands_use_list_set_and_return_structured_selection(self):
        runtime = Mock()
        result = {'engine': 'codex', 'model': 'model-b', 'changed': True}
        runtime.set_model.return_value = result
        runtime.engines.return_value = {'engine': 'codex', 'model': 'model-a', 'engines': ['codex', 'openai']}
        self.scope['text_formatter'] = Mock()
        with patch('askai.core.engine.runtime.runtime_engines', return_value=runtime):
            response = CliRunner().invoke(self.group, ['model', 'set', 'model-b'], standalone_mode=False)
            self.assertEqual(response.exit_code, 0, response.output)
            self.assertEqual(response.return_value, result)
            runtime.set_model.assert_called_once_with('model-b')
            response = CliRunner().invoke(self.group, ['engine', 'list'], standalone_mode=False)
            self.assertEqual(response.return_value['engines'], ['codex', 'openai'])
            for args in (['engine', 'set'], ['model', 'list', 'extra'], ['engine', 'openai']):
                self.assertNotEqual(CliRunner().invoke(self.group, args).exit_code, 0)

    def setUp(self):
        source = Path(__file__).parents[3] / 'main/askai/core/commander/commander.py'
        tree = ast.parse(source.read_text())
        nodes = [ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)]
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name != '_init_context':
                nodes.append(node)
            elif isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == 'COMMANDER_HELP_TPL' for target in node.targets
            ):
                nodes.append(node)
        self.scope = dict(click=click, Template=Template, dedent=dedent, HelpGroup=HelpGroup, GesturesCommand=GesturesCommand,
                          _init_context=Mock(), display_text=Mock())
        module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
        exec(compile(module, str(source), 'exec'), self.scope)
        self.group = self.scope['ask_commander']

    def test_every_registered_command_has_standard_help_without_running_callback(self):
        for name, command in self.group.commands.items():
            with self.subTest(command=name):
                original = command.callback
                callback = Mock(side_effect=AssertionError('Help must not execute command'))
                command.callback = callback
                try:
                    result = CliRunner().invoke(self.group, [name, '--help'])
                    self.assertEqual(result.exit_code, 0, result.output)
                    self.assertIn('--help', result.output)
                    self.assertIn(command.help.splitlines()[0], ' '.join(result.output.split()))
                    callback.assert_not_called()
                finally:
                    command.callback = original

    def test_custom_help_contains_usage_choices_and_history_examples(self):
        text = self.scope['commander_help']('history')
        for expected in ('/history', 'list', 'enable', 'forget', 'YYYY-MM-DD', '--help'):
            self.assertIn(expected, text)
        overview = self.scope['commander_help']()
        for name, command in self.group.commands.items():
            self.assertIn('/' + name, overview)
            self.assertIn(command.help.splitlines()[0], overview)
        with self.assertRaises(click.UsageError):
            self.scope['commander_help']('nonexistent')

    def test_lineinput_suggestions_follow_registered_commands_and_choices(self):
        suggestions = self.scope['command_suggestions']()
        for name in self.group.commands:
            self.assertIn('/' + name, suggestions)
            self.assertIn('/' + name + ' --help', suggestions)
            self.assertLess(suggestions.index('/' + name), suggestions.index('/' + name + ' --help'))
        for entry in ('/history list', '/history enable', '/history forget', '/session reset', '/session compact'):
            self.assertIn(entry, suggestions)
        self.group.add_command(click.Command('new-command', help='New registered command'))
        self.assertIn('/new-command', self.scope['commands']())
        self.assertIn('/new-command --help', self.scope['command_suggestions']())

    def test_dictate_options_reach_command_and_help_explains_silence(self):
        handler = Mock()
        self.scope['TtsSttCmd'] = handler
        result = CliRunner().invoke(self.group, [
            'dictate', '--dest-file', 'notes.txt',
        ])
        self.assertEqual(result.exit_code, 0, result.output)
        handler.dictate.assert_called_once_with('notes.txt')
        help_result = CliRunner().invoke(self.group, ['dictate', '--help'])
        self.assertIn('3 seconds', help_result.output)
        self.assertIn('copied to the clipboard', ' '.join(help_result.output.split()))

    def test_paste_waits_for_focus_change_and_supports_immediate_paste(self):
        self.scope['text_formatter'] = Mock()
        for arguments, seconds in ((['paste'], 3), (['paste', '--delay', '0'], 0)):
            with self.subTest(arguments=arguments), patch('pyperclip.paste', return_value='refined text'), patch(
                    'time.sleep') as sleep, patch('askai.core.support.clipboard.paste_into_focused_app') as paste:
                order = Mock()
                order.attach_mock(sleep, 'sleep')
                order.attach_mock(paste, 'paste')
                result = CliRunner().invoke(self.group, arguments)
                self.assertEqual(result.exit_code, 0, result.output)
                self.assertEqual(order.mock_calls, [call.sleep(seconds), call.paste()])
        help_result = CliRunner().invoke(self.group, ['paste', '--help'])
        self.assertIn('--delay', help_result.output)
        self.assertIn('without pressing Enter', ' '.join(help_result.output.split()))

    def test_empty_clipboard_and_invalid_delay_do_not_paste(self):
        self.scope['text_formatter'] = Mock()
        with patch('pyperclip.paste', return_value=''), patch('time.sleep') as sleep, patch(
                'askai.core.support.clipboard.paste_into_focused_app') as paste:
            result = CliRunner().invoke(self.group, ['paste'])
            self.assertEqual(result.exit_code, 0, result.output)
            self.scope['text_formatter'].commander_print.assert_called_once_with('The clipboard is empty.')
            for delay in ('-1', 'not-a-number'):
                self.assertNotEqual(CliRunner().invoke(self.group, ['paste', '--delay', delay]).exit_code, 0)
            sleep.assert_not_called()
            paste.assert_not_called()

    def test_paste_reports_native_permission_failure(self):
        self.scope['text_formatter'] = Mock()
        with patch('pyperclip.paste', return_value='text'), patch('time.sleep'), patch(
                'askai.core.support.clipboard.paste_into_focused_app', side_effect=RuntimeError('Enable Accessibility')):
            result = CliRunner().invoke(self.group, ['paste', '--delay', '0'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Enable Accessibility', result.output)

    def test_dictation_expected_failures_are_command_errors(self):
        import json
        import sqlite3
        from askai.exception.exceptions import InvalidInputDevice, InvalidRecognitionApiError

        errors = [FileExistsError('Already exists'), FileNotFoundError('Missing folder'),
                  PermissionError('Not writable'), ValueError('Invalid refinement'),
                  json.JSONDecodeError('Invalid JSON', 'x', 0), RuntimeError('Agent unavailable'),
                  sqlite3.OperationalError('Database unavailable'),
                  InvalidInputDevice('No microphone'), InvalidRecognitionApiError('STT unavailable')]
        for error in errors:
            with self.subTest(error=type(error).__name__):
                self.scope['TtsSttCmd'] = Mock()
                self.scope['TtsSttCmd'].dictate.side_effect = error
                with self.assertRaises(click.ClickException) as caught:
                    self.group(['dictate'], standalone_mode=False)
                self.assertEqual(str(caught.exception), str(error))

    def test_empty_commands_list_or_show_help_without_executing_other_actions(self):
        for name, command in self.group.commands.items():
            if name == 'help':
                continue
            positional = [p for p in command.params if isinstance(p, click.Argument)]
            callback = Mock()
            original = command.callback
            command.callback = callback
            try:
                result = CliRunner().invoke(self.group, [name])
                self.assertEqual(result.exit_code, 0, (name, result.output, result.exception))
                if not positional:
                    callback.assert_called_once()
                elif positional[0].default in ('list', 'start', 'toggle'):
                    callback.assert_called_once()
                    self.assertEqual(callback.call_args.kwargs[positional[0].name], positional[0].default)
                else:
                    callback.assert_not_called()
                    self.assertIn('--help', result.output)
            finally:
                command.callback = original

    def test_gestures_start_default_explicit_stop_and_completion(self):
        with patch('askai.gestures.command.start', return_value={'status': 'started'}) as start, patch(
                'askai.gestures.background.stop') as stop:
            result = CliRunner().invoke(self.group, ['gestures'], standalone_mode=False)
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.return_value, {'status': 'started'})
            start.assert_called_once_with(0)
            result = CliRunner().invoke(self.group, ['gestures', 'start', '--camera-index', '2'], standalone_mode=False)
            self.assertEqual(result.exit_code, 0, result.output)
            start.assert_called_with(2)
            start.reset_mock()
            result = CliRunner().invoke(self.group, ['gestures', 'stop'], standalone_mode=False)
            self.assertEqual(result.exit_code, 0, result.output)
            self.assertEqual(result.return_value, {'status': 'stopped'})
            start.assert_not_called()
            stop.assert_called_once_with()
            self.assertNotEqual(CliRunner().invoke(self.group, ['gestures', 'invalid']).exit_code, 0)
        suggestions = self.scope['command_suggestions']()
        self.assertIn('/gestures start', suggestions)
        self.assertIn('/gestures stop', suggestions)

    def test_both_gestures_help_routes_show_current_tables_without_starting_camera(self):
        with patch('askai.gestures.command.start') as start, patch('askai.gestures.background.stop') as stop:
            direct = CliRunner().invoke(self.group, ['gestures', '--help'], terminal_width=160)
            self.assertEqual(direct.exit_code, 0, direct.output)
            self.scope['text_formatter'] = Mock()
            self.scope['render_help'] = Mock()
            named = CliRunner().invoke(self.group, ['help', 'gestures'])
            self.assertEqual(named.exit_code, 0, named.output)
            routed_text = self.scope['render_help'].call_args.args[1]
            for text in (direct.output, routed_text):
                flat = ' '.join(click.unstyle(text).split())
                for expected in ('Gestos, ativação e cooldowns', 'Indicador', 'pinça', 'Mão espalmada',
                                 'Heavy Metal', 'Telefone', 'Joinha', 'Dois dedos', 'Quadril',
                                 '2,5 s', '0,5 s', '1 s', '45 s', '60 s', 'start', 'stop',
                                 'Para cima', 'Para baixo', '1 a 8 passos a cada 0,1 s'):
                    self.assertIn(expected, flat)
                self.assertIn('O detector de gestos irá ser desativado em 15 segundos', flat)
                self.assertNotIn('3 s contínuos', flat)
            start.assert_not_called()
            stop.assert_not_called()
