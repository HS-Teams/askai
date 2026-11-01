"""Progressive presentation paced to generated audio, retaining final Markdown."""
from askai.core.speech.presentation import NARRATION_PREFIX, reveal_text
from askai.core.speech.audio_tags import strip_audio_tags
from rich.live import Live
from rich.text import Text
from askai.cli.answer_renderer import render_answer



def stream_answer(console, text, label, duration, cancelled, narration=None):
    text = text.lstrip('\r\n')
    if not console.is_terminal:
        render_answer(console, text, label)
        return
    before = narration.before if narration else ''
    spoken = strip_audio_tags(narration.spoken) if narration else text
    marker = NARRATION_PREFIX if narration and narration.spoken else ''
    if before.strip():
        render_answer(console, before, label)
    with Live(console=console, transient=True, auto_refresh=False) as live:
        def update(partial):
            prefix = Text() if before.strip() else Text(label + ': ', style='green')
            live.update(Text.assemble(prefix, marker + partial), refresh=True)
        reveal_text(spoken, duration, cancelled, update)
    if before.strip():
        from rich.markdown import Markdown
        console.print(Markdown(marker + spoken))
        console.print()
    else:
        render_answer(console, text, label)
