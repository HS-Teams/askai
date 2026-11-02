"""Stable startup layout and exclusive terminal access for confirmations."""
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Column


def startup_progress(console):
    return Progress(
        TextColumn("{task.description}", table_column=Column(width=36, no_wrap=True, overflow="ellipsis")),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True,
        transient=True,
    )
