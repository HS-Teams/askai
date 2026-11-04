"""Exercise the application's capture actions without opening audio devices."""
import ast
import asyncio
from pathlib import Path
from threading import Event
import unittest
from unittest.mock import Mock, patch, call

from textual.app import App
from textual.binding import Binding
from askai.cli.dictation_input import cancel_requested


def capture_app(shared):
    path = Path(__file__).parents[2] / 'main/askai/tui/askai_app.py'
    source = ast.parse(path.read_text())
    app = next(node for node in source.body if isinstance(node, ast.ClassDef))
    methods = [node for node in app.body if isinstance(node, ast.FunctionDef) and node.name in {
        'check_action', 'action_cancel_capture', 'action_ptt', 'ask_and_reply'}]
    for method in methods:
        method.decorator_list = []
    bindings = next(node for node in app.body if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'BINDINGS' for target in node.targets))
    definition = ast.ClassDef(name='CaptureApp', bases=[ast.Name(id='App', ctx=ast.Load())],
                              keywords=[], body=[bindings, *methods], decorator_list=[])
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    scope = dict(App=App, Binding=Binding, shared=shared)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future, definition], type_ignores=[])),
                 str(path), 'exec'), scope)
    view = scope['CaptureApp']()
    view._capture_cancelled = Event()
    view._capture_listening = False
    view.enable_controls = Mock()
    view.askai = Mock()
    return view


class CaptureCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_escape_cancels_ptt_and_dictation_without_reading_stdin(self):
        for mode in ('ptt', 'dictation'):
            with self.subTest(mode=mode):
                shared = Mock()
                view = capture_app(shared)
                ready = Event()

                def capture(*_):
                    view._capture_listening = True
                    ready.set()
                    try:
                        self.assertTrue(view._capture_cancelled.wait(2))
                        self.assertTrue(cancel_requested())
                        return None if mode == 'ptt' else (True, None)
                    finally:
                        view._capture_listening = False

                shared.listen.side_effect = capture
                view.askai.ask_and_reply.side_effect = capture
                with patch('askai.cli.dictation_input.Keyboard.wait_keystroke') as read:
                    async with view.run_test() as pilot:
                        self.assertFalse(view.check_action('cancel_capture', ()))
                        action = view.action_ptt if mode == 'ptt' else lambda: view.ask_and_reply('/dictate')
                        task = asyncio.create_task(asyncio.to_thread(action))
                        self.assertTrue(await asyncio.to_thread(ready.wait, 1))
                        await pilot.press('escape')
                        await asyncio.wait_for(task, 3)
                        self.assertFalse(view.check_action('cancel_capture', ()))
                read.assert_not_called()
                self.assertEqual(view.enable_controls.call_args_list, [call(False), call()])

    async def test_capture_error_restores_controls(self):
        for mode in ('ptt', 'dictation'):
            with self.subTest(mode=mode):
                shared = Mock()
                shared.listen.side_effect = OSError('Microphone disconnected')
                view = capture_app(shared)
                view.askai.ask_and_reply.side_effect = OSError('Microphone disconnected')
                with self.assertRaises(OSError):
                    if mode == 'ptt':
                        view.action_ptt()
                    else:
                        view.ask_and_reply('/dictate')
                self.assertEqual(view.enable_controls.call_args_list, [call(False), call()])
