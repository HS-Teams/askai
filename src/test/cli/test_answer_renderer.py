from io import StringIO
import unittest
from unittest.mock import patch
from rich.console import Console
from askai.cli.answer_renderer import render_answer
from askai.core.model.ai_reply import AIReply


class AnswerRendererTests(unittest.TestCase):
    def test_final_answer_preserves_source_and_renders_color(self):
        source = '# Downloads\n\n1. **Fotos** — `~/Downloads/Photos`\n2. [Site](https://example.com)\n\n```python\nprint("ok")\n```'
        output = StringIO()
        console = Console(
            file=output, force_terminal=True, color_system="truecolor", width=80
        )
        from rich.markdown import Markdown

        with patch("askai.cli.answer_renderer.Markdown", wraps=Markdown) as markdown:
            render_answer(console, source)
            markdown.assert_called_once_with(source, code_theme="monokai")
        rendered = output.getvalue()
        self.assertIn("\x1b[", rendered)
        self.assertIn("Downloads", rendered)
        self.assertIn("Photos", rendered)
        self.assertNotIn("**Fotos**", rendered)
        self.assertNotIn("```", rendered)

    def test_non_terminal_output_has_no_forced_ansi(self):
        output = StringIO()
        render_answer(
            Console(file=output, force_terminal=False, color_system=None), "**Pronto**"
        )
        self.assertIn("Pronto", output.getvalue())
        self.assertNotIn("\x1b[", output.getvalue())

    def test_final_response_is_distinct_from_progress_messages(self):
        answer = AIReply.final("**Feito**")
        self.assertTrue(answer.is_final)
        self.assertTrue(answer.is_speakable)
        self.assertFalse(AIReply.mute("Listening").is_final)
        self.assertEqual(answer.message, "**Feito**")

    def test_label_and_answer_share_first_line_despite_leading_line_endings(self):
        for prefix in ("", "\r", "\n", "\r\n", "\r\n\n\r"):
            with self.subTest(prefix=repr(prefix)):
                output = StringIO()
                render_answer(Console(file=output, color_system=None, width=80),
                              prefix + "Bom dia!\n\nSegundo parágrafo.")
                lines = output.getvalue().splitlines()
                self.assertEqual(lines[0].rstrip(), "Taius: Bom dia!")
                self.assertIn("Segundo parágrafo.", output.getvalue())

    def test_only_leading_line_endings_are_removed_from_markdown(self):
        source = "    code\n\nText\n"
        with patch("askai.cli.answer_renderer.Markdown", wraps=__import__('rich.markdown', fromlist=['Markdown']).Markdown) as markdown:
            render_answer(Console(file=StringIO()), "\r\n" + source)
            markdown.assert_called_once_with(source, code_theme="monokai")
