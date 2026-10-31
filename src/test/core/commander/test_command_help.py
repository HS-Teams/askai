"""Test the real Click registry without loading devices or personal stores."""
import ast
from pathlib import Path
from string import Template
from textwrap import dedent
import unittest
from unittest.mock import Mock
import click
from click.testing import CliRunner
from askai.cli.help_formatter import HelpGroup


class CommandHelpTests(unittest.TestCase):
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
        self.scope = dict(click=click, Template=Template, dedent=dedent, HelpGroup=HelpGroup,
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
        for entry in ('/history list', '/history enable', '/history forget', '/session reset', '/session compact'):
            self.assertIn(entry, suggestions)
        self.group.add_command(click.Command('new-command', help='New registered command'))
        self.assertIn('/new-command', self.scope['commands']())
        self.assertIn('/new-command --help', self.scope['command_suggestions']())
