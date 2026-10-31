from io import StringIO
import unittest
from unittest.mock import Mock
from rich.console import Console
from askai.cli.confirmation import Confirmation, show_confirmation


class ConfirmationTests(unittest.TestCase):
    def test_options_support_numbers_and_voice(self):
        for answer, expected in [
            ("1", True),
            ("Sim.", True),
            ("2", False),
            ("Não.", False),
            ("", False),
            (None, False),
        ]:
            with self.subTest(answer=answer):
                self.assertEqual(
                    Confirmation(Mock(return_value=answer), Mock())("Abrir arquivo?"),
                    expected,
                )

    def test_ambiguous_input_does_not_approve(self):
        read = Mock(side_effect=["talvez", "2"])
        self.assertFalse(Confirmation(read, Mock())("Executar?"))
        self.assertEqual(read.call_count, 2)

    def test_panel_is_explicit_and_does_not_interpret_command_markup(self):
        output = StringIO()
        show_confirmation(
            Console(file=output, width=90, color_system=None),
            "Executar [red]arquivo[/red]?",
        )
        text = output.getvalue()
        for expected in [
            "CONFIRMATION REQUIRED",
            "(1) Yes, allow     [(2) No, cancel]",
            "Enter cancels",
            "[red]arquivo[/red]",
        ]:
            self.assertIn(expected, text)

    def test_all_panel_chrome_uses_injected_translator(self):
        output = StringIO()
        translate = Mock(side_effect=lambda text: "LOCALIZED " + text)
        show_confirmation(
            Console(file=output, width=120, color_system=None), "message", translate
        )
        for source in (
            "Yes, allow",
            "No, cancel",
            "This action only. Enter cancels.",
            "CONFIRMATION REQUIRED",
        ):
            translate.assert_any_call(source)
        self.assertIn("LOCALIZED", output.getvalue())

    def test_default_is_bracketed_and_enter_cancels(self):
        labels = {"Yes, allow": "Sim, permitir", "No, cancel": "Não, cancelar"}
        translate = lambda text: labels.get(text, text)
        read = Mock(return_value="")
        self.assertFalse(Confirmation(read, Mock(), translate)("Abrir?"))
        read.assert_called_once_with("(1) Sim, permitir     [(2) Não, cancelar]")
        output = StringIO()
        show_confirmation(Console(file=output, width=100, color_system=None), "Abrir?", translate)
        self.assertIn("(1) Sim, permitir     [(2) Não, cancelar]", output.getvalue())
