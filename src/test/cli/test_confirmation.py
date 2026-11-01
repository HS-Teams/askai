from io import StringIO
import unittest
from unittest.mock import Mock
from rich.console import Console
from askai.cli.confirmation import Confirmation, show_confirmation


class ConfirmationTests(unittest.TestCase):
    def test_selection_echoes_localized_label_once_before_return(self):
        labels = {'Yes, allow': 'Sim, permitir', 'No, cancel': 'Não, cancelar'}
        for key, allowed in [('1', True), ('2', False), ('\r', False), ('\x1b', False)]:
            with self.subTest(key=key):
                echo = Mock()
                confirm = Confirmation(Mock(side_effect=['x', key]), Mock(),
                                       translate=labels.__getitem__, echo=echo)
                self.assertEqual(confirm('Permitir?'), allowed)
                echo.assert_called_once_with('Sim, permitir' if allowed else 'Não, cancelar')


    def test_options_accept_only_expected_keys(self):
        for answer, expected in [
            ("1", True),
            ("\r", False),
            ("2", False),
            ("\x1b", False),
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
        read.assert_called_once_with("")
        output = StringIO()
        show_confirmation(Console(file=output, width=100, color_system=None), "Abrir?", translate)
        self.assertIn("(1) Sim, permitir     [(2) Não, cancelar]", output.getvalue())

    def test_invalid_keys_are_ignored_without_reprinting(self):
        read, show = Mock(side_effect=['s', 'y', 'x', '3', '1']), Mock()
        self.assertTrue(Confirmation(read, show)('Allow?'))
        show.assert_called_once_with('Allow?')

    def test_grants_are_below_question_in_light_gray(self):
        console = Mock()
        grants = ['askai.grants.camera.preview.local', 'askai.grants.desktop.pointer.move']
        show_confirmation(console, 'Allow?', grants=grants)
        body = console.print.call_args.args[0].renderable
        self.assertTrue(body.plain.startswith('Allow?\n' + '\n'.join(grants)))
        self.assertTrue(any(span.style == 'grey70' for span in body.spans))

    def test_scope_is_passed_separately_from_translated_message(self):
        show = Mock()
        Confirmation(Mock(return_value='1'), show)('Allow?', grants=['askai.grants.camera.preview.local'])
        show.assert_called_once_with('Allow?', grants=['askai.grants.camera.preview.local'])
