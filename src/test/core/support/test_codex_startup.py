"""Exercise startup methods without loading UI, audio devices or settings storage."""
import ast
from pathlib import Path
from queue import SimpleQueue
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock

from askai.core.agents.contracts import AgentError
from askai.core.support.startup import run_startup_tasks


def startup_method(relative_path, namespace):
    source = Path(__file__).parents[3] / 'main' / relative_path
    tree = ast.parse(source.read_text())
    method = next(node for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name == '_startup')
    method.decorator_list = []

    class InjectImports(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            return ast.copy_location(ast.Pass(), node)

    method = InjectImports().visit(method)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 str(source), 'exec'), namespace)
    return namespace['_startup']


class CodexStartupTests(unittest.TestCase):
    def environment(self, directory, interactive):
        namespace = {name: MagicMock() for name in (
            'os', 'AskAiEvents', 'ASKAI_BUS_NAME', 'VOICE_INPUT_EVENT', 'REPLY_EVENT',
            'TTS_FALLBACK_EVENT', 'MIC_LISTENING_EVENT', 'DEVICE_CHANGED_EVENT',
            'MODE_CHANGED_EVENT', 'cli_output', 'startup_progress', 'Progress', 'shared',
            'nltk', 'CACHE_DIR', 'cache', 'command_suggestions', 'rag', 'KeyboardInput',
            'scheduler', 'recorder', 'player', 'screen', 'AIReply', 'AppIcons',
            'now', 'TIME_FORMAT', 'log',
        )}
        namespace.update(Path=Path, run_startup_tasks=run_startup_tasks,
                         configs=SimpleNamespace(is_interactive=interactive, is_cache=False, is_speak=False),
                         msg=SimpleNamespace(t=lambda text: text),
                         Charset=SimpleNamespace(UTF_8=SimpleNamespace(val='utf-8')))
        view = MagicMock()
        view.console_path = Path(directory) / 'console.txt'
        view._startup_notices = SimpleQueue()
        view._pending_tts_fallback = None
        return namespace, view

    def test_cli_and_tui_prepare_before_becoming_ready(self):
        for relative_path, interactive in (
            ('askai/core/askai_cli.py', True), ('askai/core/askai_cli.py', False),
            ('askai/tui/askai_app.py', True),
        ):
            with self.subTest(path=relative_path, interactive=interactive), TemporaryDirectory() as directory:
                namespace, view = self.environment(directory, interactive)
                calls = Mock()
                calls.attach_mock(namespace['shared'].engine.backend.prepare, 'connect')
                calls.attach_mock(namespace['log'].info, 'ready')
                startup_method(relative_path, namespace)(view)
                self.assertEqual([call[0] for call in calls.mock_calls], ['connect', 'ready'])

    def test_login_failure_stops_startup_without_reporting_ready(self):
        for relative_path in ('askai/core/askai_cli.py', 'askai/tui/askai_app.py'):
            with self.subTest(path=relative_path), TemporaryDirectory() as directory:
                namespace, view = self.environment(directory, True)
                namespace['shared'].engine.backend.prepare.side_effect = AgentError('Login required')
                with self.assertRaisesRegex(AgentError, 'Login required'):
                    startup_method(relative_path, namespace)(view)
                namespace['log'].info.assert_not_called()
                namespace['recorder'].setup.assert_not_called()
