"""Microphone changes are system notifications, never assistant speech."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class DeviceNotificationTests(unittest.TestCase):
    def test_both_views_notify_without_reply_or_speech(self):
        for filename in ('core/askai_cli.py', 'tui/askai_app.py'):
            with self.subTest(view=filename):
                path = Path(__file__).parents[2] / 'main/askai' / filename
                method = next(n for n in ast.walk(ast.parse(path.read_text()))
                              if isinstance(n, ast.FunctionDef) and n.name == '_cb_device_changed_event')
                formatter, shared, view = Mock(), Mock(), Mock()
                msg = SimpleNamespace(t=lambda s: 'Sistema' if s == 'System' else s,
                                      device_switch=lambda s: '\nDispositivo: ' + s + '\n',
                                      translate=lambda s: s)
                scope = dict(Event=object, cursor=Mock(), msg=msg,
                             text_formatter=formatter, shared=shared)
                module = ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[]))
                exec(compile(module, str(path), 'exec'), scope)
                scope[method.name](view, SimpleNamespace(args=SimpleNamespace(device=(1, 'Microphone'))))
                view._reply.assert_not_called()
                shared.speech.speak.assert_not_called()
                if filename.startswith('core'):
                    notice = formatter.console.print.call_args.args[0]
                    self.assertTrue(notice.plain.startswith('Sistema: Dispositivo:'))
                    self.assertNotIn('Taius', notice.plain)
                else:
                    self.assertEqual(view.call_later.call_args.kwargs['title'], 'Sistema')
                    self.assertEqual(view.call_later.call_args.args[0], view.notify)
