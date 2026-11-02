import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from askai.core.model.ai_reply import AIReply


class SystemNoticesTests(unittest.TestCase):
    def test_all_gesture_notices_are_system_and_never_spoken(self):
        path = Path(__file__).resolve().parents[2] / 'main/askai/gestures/command.py'
        tree = ast.parse(path.read_text())
        notify = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'notify')
        messages = next(n.value for n in tree.body if isinstance(n, ast.Assign) and
                        any(isinstance(t, ast.Name) and t.id == 'MESSAGES' for t in n.targets))
        events = Mock()
        scope = dict(AIReply=AIReply, MESSAGES=ast.literal_eval(messages), events=events)
        exec(compile(ast.Module(body=[notify], type_ignores=[]), str(path), 'exec'), scope)
        with patch('askai.gestures.sfx._play'):
            for kind in scope['MESSAGES']:
                scope['notify'](kind)
                reply = events.reply.emit.call_args.kwargs['reply']
                self.assertTrue(reply.is_system)
                self.assertFalse(reply.is_speakable)
