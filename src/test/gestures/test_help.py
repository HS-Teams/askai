from io import StringIO
import unittest
from unittest.mock import patch
from rich.console import Console
from askai.cli.gestures_help import gesture_tables
from askai.cli.help_formatter import render_help


class GestureHelpTests(unittest.TestCase):
    def test_help_reads_current_settings_instead_of_copying_delays(self):
        with patch('askai.gestures.session.RESUME_HOLD_SECONDS', 3.25), patch(
                'askai.gestures.session.PAUSE_STOP_SECONDS', 25.), patch(
                'askai.gestures.controller.GestureController.DOUBLE_CLICK_COOLDOWN_SECONDS', 1.75):
            text = ' '.join(gesture_tables(160).split())
        self.assertIn('3,25 s contínuos', text)
        self.assertIn('25 s', text)
        self.assertIn('1,75 s após disparar', text)

    def test_tables_render_at_standard_terminal_width_without_ansi_or_overflow(self):
        text = gesture_tables(80)
        output = StringIO()
        console = Console(file=output, width=80, force_terminal=False)
        render_help(console, text, overview=False)
        rendered = output.getvalue()
        self.assertNotIn('\x1b[', rendered)
        self.assertTrue(all(len(line) <= 80 for line in rendered.splitlines()))
        for label in ('Gestos, ativação', 'Heavy Metal', 'Pausar controle', '45 s', '60 s', 'Para cima', 'Para baixo'):
            self.assertIn(label, rendered)
        self.assertIn('1 a 8 passos a cada 0,1 s', ' '.join(rendered.split()))
        self.assertNotIn('ângulo entre braço', rendered)
        self.assertIn('75% da altura até o quadril', ' '.join(rendered.split()))
        self.assertIn('25% restantes dão margem para fechar a pinça', ' '.join(rendered.split()))
        self.assertIn('PTT ou ditado', rendered)
        self.assertIn('o ponteiro fica parado, inclusive na faixa neutra', ' '.join(rendered.split()))
        self.assertIn('os gestos são retomados após 0,5 s', ' '.join(rendered.split()))
        self.assertIn('Todos os outros gestos ficam bloqueados durante a rolagem', ' '.join(rendered.split()))
        self.assertIn('Durante o PTT ou ditado, a pausa não conta como inatividade', ' '.join(rendered.split()))
