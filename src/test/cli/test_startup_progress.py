import unittest
from io import StringIO
from types import SimpleNamespace
from unittest.mock import Mock
from rich.console import Console
from askai.cli.startup_progress import startup_progress


class StartupProgressTests(unittest.TestCase):
    def test_long_labels_keep_one_line_and_same_total_width(self):
        console = Console(file=StringIO(), width=100, color_system=None)
        progress = startup_progress(console)
        task = progress.add_task('Loading', total=9)
        lines = []
        for label in ('Loading', 'Preparing gesture controller and camera ' * 5):
            progress.update(task, description=label)
            with console.capture() as output:
                console.print(progress.get_renderable())
            rendered = output.get().splitlines()
            self.assertEqual(len(rendered), 1)
            lines.append(rendered[0])
        self.assertEqual(len(lines[0]), len(lines[1]))
        self.assertIn('…', lines[1])

    def test_width_is_capped_and_adapts_to_terminal_resize(self):
        console = Console(file=StringIO(), width=160, color_system=None)
        progress = startup_progress(console)
        progress.add_task('Preparing gesture controller and camera ' * 5, total=9)
        for width in (160, 80, 60, 40):
            console.width = width
            with self.subTest(width=width), console.capture() as output:
                console.print(progress.get_renderable())
            lines = output.get().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertLessEqual(len(lines[0]), min(width, 80))

