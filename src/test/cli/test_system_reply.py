import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from askai.core.model.ai_reply import AIReply


class SystemReplyTests(unittest.TestCase):
    def test_status_is_not_speakable(self):
        reply = AIReply.system('Gesture control started.')
        self.assertTrue(reply.is_system)
        self.assertFalse(reply.is_speakable)
        self.assertFalse(reply.is_final)

    def test_cli_and_tui_status_bypass_assistant_reply(self):
        root = Path(__file__).resolve().parents[2] / 'main/askai'
        for path, method in ((root / 'core/askai_cli.py', '_display_reply_event'),
                             (root / 'tui/askai_app.py', '_cb_reply_event')):
            tree = ast.parse(path.read_text())
            node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == method)
            node.returns = None
            for arg in node.args.args:
                arg.annotation = None
            formatter, view = Mock(), Mock()
            scope = dict(AIReply=AIReply, msg=Mock(t=lambda text: 'Sistema', translate=lambda text: text))
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
            event = SimpleNamespace(args=SimpleNamespace(reply=AIReply.system('Stopped.')))
            with patch.dict('sys.modules', {'askai.core.support.text_formatter': SimpleNamespace(text_formatter=formatter)}):
                scope[method](view, event)
            view._reply.assert_not_called()
            view._reply_error.assert_not_called()
            if method == '_display_reply_event':
                self.assertEqual(formatter.console.print.call_args.args[0].plain, '  Sistema: Stopped.')
            else:
                self.assertEqual(view.notify.call_args.kwargs['title'], '  Sistema')

    def test_startup_system_notice_is_retained_until_screen_is_ready(self):
        from queue import SimpleQueue
        path = Path(__file__).resolve().parents[2] / 'main/askai/core/askai_cli.py'
        tree = ast.parse(path.read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == '_cb_reply_event')
        node.returns = None
        for arg in node.args.args:
            arg.annotation = None
        scope = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        view = SimpleNamespace(_ready=False, _startup_notices=SimpleQueue())
        event = SimpleNamespace(args=SimpleNamespace(reply=AIReply.system('Gesture control started.')))
        scope['_cb_reply_event'](view, event)
        self.assertIs(view._startup_notices.get_nowait(), event)

    def test_system_notice_is_queued_if_prompt_opens_during_translation(self):
        from queue import Queue
        from types import MethodType
        from askai.cli import prompt_input
        path = Path(__file__).resolve().parents[2] / 'main/askai/core/askai_cli.py'
        tree = ast.parse(path.read_text())
        nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
                 and node.name in ('_cb_reply_event', '_display_reply_event')]
        for node in nodes:
            node.returns = None
            for arg in node.args.args:
                arg.annotation = None
        editor = SimpleNamespace(messages=Queue())

        def translate(text):
            prompt_input._active = editor
            return text

        scope = dict(AIReply=AIReply, msg=SimpleNamespace(t=lambda _: 'Sistema', translate=translate))
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), scope)
        view = SimpleNamespace(_ready=True)
        view._display_reply_event = MethodType(scope['_display_reply_event'], view)
        formatter = Mock()
        event = SimpleNamespace(args=SimpleNamespace(reply=AIReply.system('Ajuste a posição.')))
        with patch.object(prompt_input, '_active', None), patch.dict('sys.modules', {
                'askai.core.support.text_formatter': SimpleNamespace(text_formatter=formatter)}):
            scope['_cb_reply_event'](view, event)
            formatter.console.print.assert_not_called()
            self.assertEqual(editor.messages.qsize(), 1)
            editor.messages.get_nowait()()
        formatter.console.print.assert_called_once()
        self.assertEqual(formatter.console.print.call_args.args[0].plain, '  Sistema: Ajuste a posição.')
