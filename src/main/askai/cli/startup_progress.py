"""Stable startup layout and exclusive terminal access for confirmations."""
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.table import Column


class StartupProgress(Progress):
    MAX_WIDTH = 80

    def __init__(self, *columns, console, **kwargs):
        self._startup_console = console
        super().__init__(*columns, console=console, **kwargs)

    def make_tasks_table(self, tasks):
        table = super().make_tasks_table(tasks)
        table.width = min(self.MAX_WIDTH, self._startup_console.width)
        return table


def startup_progress(console):
    return StartupProgress(
        TextColumn("{task.description}", table_column=Column(width=36, no_wrap=True, overflow="ellipsis")),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True,
        transient=True,
    )
