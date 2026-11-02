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
