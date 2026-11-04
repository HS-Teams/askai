"""Shared CLI console and presentation using the answer Markdown theme."""
from hspylib.modules.cli.vt100.vt_code import VtCode
from hspylib.modules.cli.vt100.vt_color import VtColor
from rich.console import Console
from rich.text import Text
from askai.cli.answer_renderer import render_answer


console = Console(log_time=False, log_path=False)


def render_message(text: str, label: str | None = None) -> None:
    render_answer(console, str(text), label)


def render_command(text: str) -> None:
    render_message(text, " Commander")


def render_text(text: str, label: str | None = None, style: str = "") -> None:
    if label:
        console.print(Text(label + ": ", style=style), end="")
    console.print(Text.from_ansi(VtColor.colorize(VtCode.decode(str(text)))))
