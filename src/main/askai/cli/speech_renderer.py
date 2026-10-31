"""Progressive presentation paced to generated audio, retaining final Markdown."""
from askai.core.speech.presentation import reveal_text
from rich.live import Live
from rich.text import Text
from askai.cli.answer_renderer import render_answer



def stream_answer(console, text, label, duration, cancelled):
    text = text.lstrip('\r\n')
    if not console.is_terminal:
        render_answer(console, text, label)
        return
    with Live(console=console, transient=True, auto_refresh=False) as live:
        def update(partial):
            live.update(Text.assemble((label + ': ', 'green'), partial), refresh=True)
        reveal_text(text, duration, cancelled, update)
    render_answer(console, text, label)
