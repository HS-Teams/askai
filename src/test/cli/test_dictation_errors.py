"""Dictation failures cross the real Click callback and return to the chat loop."""
import ast
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import click
from askai.core.speech import dictation
from askai.core.engine.runtime import between_turns


class DictationErrorTests(unittest.TestCase):
    def load(self, relative, name, scope):
        path = Path(__file__).parents[2] / 'main/askai' / relative
        node = next(n for n in ast.walk(ast.parse(path.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
        module = ast.fix_missing_locations(ast.Module(body=[future, node], type_ignores=[]))
        exec(compile(module, str(path), 'exec'), scope)

    def test_existing_destination_and_invalid_refinement_return_to_prompt(self):
        with TemporaryDirectory() as directory:
            destination = Path(directory) / 'notes.txt'
            destination.write_text('existing content')
            for scenario in ('existing', 'invalid_json'):
                with self.subTest(scenario=scenario):
                    if scenario == 'invalid_json':
                        destination = Path(directory) / 'new.txt'
                    def run_dictation(_):
                        dictation.validate_destination(destination)
                        dictation.save_original(destination, 'Original API text')
                        dictation.refine('Original API text', 'instructions', Mock(return_value='invalid'))
                    group = click.Group()
                    scope = dict(click=click, ask_commander=group,
                                 TtsSttCmd=SimpleNamespace(dictate=run_dictation))
                    self.load('core/commander/commander.py', 'dictate', scope)
                    events, reply = Mock(), Mock()
                    scope.update(shared=Mock(), re=re, RE_ASKAI_CMD=r'^/.*', between_turns=between_turns,
                                 command_args=lambda match: ['dictate'], AIProcessor=object,
                                 events=events, AIReply=reply, msg=SimpleNamespace(t=lambda text: text),
                                 ClickException=click.ClickException, UsageError=click.UsageError)
                    for name in ('ImpossibleQuery', 'DocumentsNotFound', 'MaxInteractionsReached',
                                 'InaccurateResponse', 'ValidationError'):
                        scope[name] = type(name, (Exception,), {})
                    self.load('core/askai.py', 'ask_and_reply', scope)
                    view = SimpleNamespace(mode=SimpleNamespace(processor=object()))
                    with patch('askai.core.commander.command_results.execute_command',
                               side_effect=lambda args, **kwargs: group(args, standalone_mode=False)):
                        self.assertEqual(scope['ask_and_reply'](view, '/dictate'), (True, None))
                    events.reply.emit.assert_called_once_with(reply=reply.error.return_value)
                    if scenario == 'existing':
                        self.assertEqual(destination.read_text(), 'existing content')
                    else:
                        self.assertEqual(dictation.original_path(destination).read_text(), 'Original API text')
                        self.assertFalse(destination.exists())
