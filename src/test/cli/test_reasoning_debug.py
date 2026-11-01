import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from askai.core.model.ai_reply import AIReply


class ReasoningDebugTests(unittest.TestCase):
    def test_summary_is_debug_only_and_never_spoken_in_either_view(self):
        for filename in ('core/askai_cli.py', 'tui/askai_app.py'):
            for enabled in (True, False):
                with self.subTest(filename=filename, enabled=enabled):
                    path = Path(__file__).parents[2] / 'main/askai' / filename
                    method = next(n for n in ast.walk(ast.parse(path.read_text()))
                                  if isinstance(n, ast.FunctionDef) and n.name == '_agent_event')
                    events, shared = Mock(), Mock()
                    scope = dict(events=events, shared=shared, AIReply=AIReply,
                                 configs=SimpleNamespace(is_debug=enabled, is_speak=True))
                    module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
                    exec(compile(module, str(path), 'exec'), scope)
                    scope['_agent_event'](Mock(), SimpleNamespace(kind='reasoning_summary', data={'text': 'Checking sources.'}))
                    shared.speech.speak.assert_not_called()
                    if enabled:
                        reply = events.reply.emit.call_args.kwargs['reply']
                        self.assertTrue(reply.is_debug)
                        self.assertFalse(reply.is_speakable)
                        self.assertFalse(reply.is_final)
                        self.assertFalse(reply.match(is_debug=False))
                        self.assertIn('Debug · Codex:', reply.message)
                    else:
                        events.reply.emit.assert_not_called()
