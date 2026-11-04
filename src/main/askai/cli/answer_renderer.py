"""Render the final answer locally without rewriting its Markdown content."""

from rich.markdown import Markdown
from rich.text import Text
from rich.theme import Theme

ANSWER_THEME = Theme(
    {
        "markdown.h1": "bold cyan",
        "markdown.h1.border": "cyan",
        "markdown.h2": "bold cyan",
        "markdown.h3": "bold magenta",
        "markdown.strong": "bold bright_cyan",
        "markdown.em": "italic",
        "markdown.code": "bold yellow",
        "markdown.link": "underline bright_blue",
        "markdown.item.number": "bold cyan",
        "markdown.item.bullet": "cyan",
        "markdown.table.header": "bold cyan",
        "markdown.table.border": "dim cyan",
    }
)


def render_answer(console, markdown: str, label: str | None = "Taius") -> None:
    if label:
        console.print(Text(f"{label}: ", style="green"), end="")
    with console.use_theme(ANSWER_THEME):
        console.print(Markdown(markdown.lstrip("\r\n"), code_theme="monokai"))
    console.print()
