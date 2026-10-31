"""Consistent terminal colors for Click help without changing its content."""
import re

import click
from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme


HELP_THEME = Theme({
    'markdown.h1': 'bold green',
    'markdown.h1.border': 'green',
    'markdown.code': 'bold cyan',
    'markdown.table.header': 'bold cyan',
    'markdown.table.border': 'dim green',
    'markdown.strong': 'bold yellow',
})


def color_help(text: str) -> str:
    pattern = r'(?m)^(?:Usage|Options|Commands):|(?<!\w)--?[\w-]+|/[\w-]+|\[[^\]\n]+\]|<[^>\n]+>'

    def paint(match):
        token = match.group()
        color = 'green' if token.endswith(':') else 'cyan' if token.startswith(('/', '-')) else 'yellow'
        return click.style(token, fg=color, bold=True)

    return re.sub(pattern, paint, text)


class HelpCommand(click.Command):
    def get_help(self, ctx):
        return color_help(super().get_help(ctx))


class HelpGroup(click.Group):
    command_class = HelpCommand

    def get_help(self, ctx):
        return color_help(super().get_help(ctx))


def render_help(console, text: str, *, overview: bool) -> None:
    with console.use_theme(HELP_THEME):
        console.print(Markdown(text) if overview else Text.from_ansi(text))
