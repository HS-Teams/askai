from io import StringIO
import unittest
import click
from click.testing import CliRunner
from rich.console import Console
from askai.cli.help_formatter import HelpCommand, color_help, render_help


class HelpFormatterTests(unittest.TestCase):
    def test_colors_do_not_change_help_content(self):
        source = 'Usage: /history [OPTIONS] [VALUE]\nOptions:\n  --help  Show help.'
        colored = color_help(source)
        self.assertIn('\x1b[', colored)
        self.assertEqual(click.unstyle(colored), source)

    def test_standard_help_respects_terminal_color_selection(self):
        command = HelpCommand('history', help='Conversation history.')
        for enabled in (True, False):
            result = CliRunner().invoke(command, ['--help'], color=enabled)
            self.assertEqual(result.exit_code, 0)
            self.assertEqual('\x1b[' in result.output, enabled)

    def test_overview_and_detail_render_without_ansi_leaks(self):
        for overview, text in ((True, '# Help\n\n| Command | Description |\n| --- | --- |\n| `/history` | History |'),
                               (False, color_help('Usage: /history [OPTIONS]'))):
            for terminal in (True, False):
                output = StringIO()
                render_help(Console(file=output, force_terminal=terminal, color_system='standard' if terminal else None),
                            text, overview=overview)
                self.assertIn('/history', output.getvalue())
                self.assertEqual('\x1b[' in output.getvalue(), terminal)
