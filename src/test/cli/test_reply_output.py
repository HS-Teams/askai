"""Assistant replies and commands share a renderer without rewriting Markdown."""
import ast
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from rich.console import Console
from askai.cli import output
from askai.core.model.ai_reply import AIReply


class ReplyOutputTests(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()
        self.console = Console(file=self.buffer, color_system=None, width=160)
        self.shared = SimpleNamespace(speech=Mock())
        self.configs = SimpleNamespace(is_speak=False, is_keep_context=False)
        self.events = Mock()
        path = Path(__file__).parents[2] / 'main/askai/core/askai_cli.py'
        tree = ast.parse(path.read_text())
        methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                   and node.name in ('_reply', '_reply_error')]
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        self.scope = dict(shared=self.shared, configs=self.configs, AIReply=AIReply,
                          msg=SimpleNamespace(translate=lambda text: text),
                          log=Mock(), events=self.events)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[future, *methods], type_ignores=[])),
                     str(path), 'exec'), self.scope)
        self.view = SimpleNamespace(mode=SimpleNamespace(icon=''))
        console = patch.object(output, 'console', self.console)
        console.start()
        self.addCleanup(console.stop)

    def test_final_info_and_error_share_label_spacing_and_narration_marker(self):
        for reply in (AIReply.final('<TTS>Como posso ajudar?</TTS>'),
                      AIReply.info('Como posso ajudar?'), AIReply.error('Falha no áudio')):
            with self.subTest(reply=reply):
                self.buffer.truncate(0)
                self.buffer.seek(0)
                self.scope['_reply_error' if reply.is_error else '_reply'](self.view, reply)
                first_line = self.buffer.getvalue().splitlines()[0].rstrip()
                expected = 'Error: Falha no áudio' if reply.is_error else 'Como posso ajudar?'
                self.assertEqual(first_line, ' Taius: 降 ' + expected)
                self.assertNotIn('%', first_line)
                self.shared.speech.speak.assert_not_called()

    def test_error_remains_visible_and_silent_when_speech_is_enabled(self):
        self.configs.is_speak = True
        self.scope['_reply_error'](self.view, AIReply.error('Falha'))
        self.assertIn(' Taius: 降 Error: Falha', self.buffer.getvalue())
        self.shared.speech.speak.assert_not_called()

    def test_info_speech_uses_the_same_visual_marker_without_speaking_it(self):
        self.configs.is_speak = True
        self.scope['_reply'](self.view, AIReply.info('Como posso ajudar?'))
        call = self.shared.speech.speak.call_args
        self.assertEqual(call.args[0], 'Como posso ajudar?')
        call.kwargs['present'](1.0, Mock())
        self.assertIn(' Taius: 降 Como posso ajudar?', self.buffer.getvalue())

    def test_speech_failure_still_renders_the_normalized_reply(self):
        self.configs.is_speak = True
        self.scope['_reply'](self.view, AIReply.info('Como posso ajudar?'))
        call = self.shared.speech.speak.call_args
        self.assertEqual(call.args[0], 'Como posso ajudar?')
        self.assertEqual(call.kwargs['wait'], True)
        call.args[1](RuntimeError('TTS indisponível'))
        self.assertIn(' Taius: 降 Como posso ajudar?', self.buffer.getvalue())
        self.assertEqual(self.events.reply.emit.call_args.kwargs['reply'].message, 'TTS indisponível')

    def test_command_and_unlabelled_markdown_preserve_links_and_literal_content(self):
        source = 'Taius: **Pronto** [Site](https://example.com) `a_b`'
        from rich.markdown import Markdown
        with patch('askai.cli.answer_renderer.Markdown', wraps=Markdown) as markdown:
            output.render_command(source)
            markdown.assert_called_once_with(source, code_theme='monokai')
        self.assertTrue(self.buffer.getvalue().startswith(' Commander: Taius: Pronto'))
        self.buffer.truncate(0)
        self.buffer.seek(0)
        output.render_message('Sem prefixo')
        self.assertEqual(self.buffer.getvalue().strip(), 'Sem prefixo')

    def test_plain_output_keeps_brackets_and_uses_a_separate_label(self):
        output.render_text('[audio] {motivo}', 'Aviso', style='yellow')
        self.assertEqual(self.buffer.getvalue().strip(), 'Aviso: [audio] {motivo}')
