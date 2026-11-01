import ast
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import click
from rich.console import Console

from askai.core.commander import command_results as results


class CommandResultTests(unittest.TestCase):
    def setUp(self):
        self.stream = StringIO()
        self.console = Console(file=self.stream, width=120, color_system=None)
        self.group = click.Group()
        commander = ModuleType('askai.core.commander.commander')
        commander.ask_commander = self.group
        formatter = ModuleType('askai.core.support.text_formatter')
        formatter.text_formatter = SimpleNamespace(console=self.console)
        self.modules = patch.dict('sys.modules', {commander.__name__: commander, formatter.__name__: formatter})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        results.communication.clear()

    def test_command_output_is_visible_live_and_returned_with_structured_data(self):
        @self.group.command()
        def voices():
            self.console.print('12. Alice')
            self.assertIn('12. Alice', self.stream.getvalue())
            return {'voices': [{'index': 12, 'name': 'Alice'}]}

        result = results.execute_command(['voices'])
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['data']['voices'][0]['name'], 'Alice')
        self.assertIn('12. Alice', result['output'])
        self.assertEqual(self.stream.getvalue().count('12. Alice'), 1)
        self.assertEqual(results.recent_results('voices'), [result])

    def test_click_failures_preserve_output_and_are_available_for_diagnosis(self):
        @self.group.command()
        def broken():
            self.console.print('Starting command')
            raise click.ClickException('Voice service unavailable')

        result = results.execute_command(['broken'])
        self.assertEqual(result['status'], 'failed')
        self.assertIn('Starting command', result['output'])
        self.assertEqual(results.recent_results('broken'), [result])
        self.assertEqual(results.command_diagnostics('broken')['entries'], [
            {'command': 'broken', 'error': 'Voice service unavailable'}])
        self.assertIs(self.console.file, self.stream)
        with self.assertRaises(click.ClickException):
            results.execute_command(['broken'], raise_errors=True)

    def test_stdout_output_is_returned_and_forwarded_without_duplicates(self):
        @self.group.command()
        def plain():
            print('Current setting')
            self.console.print('Command finished')

        with redirect_stdout(self.stream):
            result = results.execute_command(['plain'])
        self.assertIn('Current setting', result['output'])
        self.assertIn('Command finished', result['output'])
        self.assertEqual(self.stream.getvalue().count('Current setting'), 1)
        self.assertEqual(self.stream.getvalue().count('Command finished'), 1)

    def test_other_threads_output_is_visible_but_not_returned_as_command_output(self):
        from threading import Thread

        @self.group.command()
        def threaded():
            worker = Thread(target=lambda: self.console.print('Unrelated background output'))
            worker.start()
            worker.join()
            self.console.print('Command result')

        result = results.execute_command(['threaded'])
        self.assertNotIn('Unrelated background output', result['output'])
        self.assertIn('Unrelated background output', self.stream.getvalue())
        self.assertIn('Command result', result['output'])

    def test_deferred_result_lookup_does_not_require_working_speech_services(self):
        results.record_result({'command': 'dictate', 'status': 'completed', 'output': 'Saved'})
        state = results.current_state('dictate')
        self.assertEqual(state['results'][0]['output'], 'Saved')

    def test_structured_failure_is_not_reported_as_completed(self):
        @self.group.command()
        def voices():
            return {'status': 'failed', 'error': 'Invalid voice index'}

        result = results.execute_command(['voices'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(results.command_diagnostics('voices')['entries'][0]['error'], 'Invalid voice index')

    def test_console_capture_is_bounded_without_truncating_the_ui(self):
        @self.group.command()
        def large():
            self.console.print('x' * (results.MAX_OUTPUT + 100), soft_wrap=True)

        result = results.execute_command(['large'])
        self.assertTrue(result['output_truncated'])
        self.assertEqual(len(result['output']), results.MAX_OUTPUT)
        self.assertGreater(len(self.stream.getvalue()), results.MAX_OUTPUT)

    def test_recent_results_are_bounded_filtered_and_copied(self):
        for index in range(results.MAX_RESULTS + 2):
            results.record_result({'status': 'completed', 'command': str(index)})
        snapshot = results.recent_results()
        self.assertEqual(len(snapshot), results.MAX_RESULTS)
        snapshot[-1]['command'] = 'changed'
        self.assertNotEqual(results.recent_results()[-1]['command'], 'changed')
        self.assertEqual(results.recent_results('0'), [])

    def test_live_state_uses_current_catalogue_not_old_command_output(self):
        speech = SimpleNamespace(model_name='eleven_v4', voice='voice12', provider_name='ElevenLabs',
                                 voices=lambda: ['Voice 0', 'Voice 1', 'Current voice'])
        shared = ModuleType('askai.core.support.shared_instances')
        shared.shared = SimpleNamespace(speech=SimpleNamespace(tts=speech), engine=Mock(ai_model_name=lambda: 'test-model'))
        configs = ModuleType('askai.core.askai_configs')
        configs.configs = SimpleNamespace(engine='codex', tts_engine='ElevenLabs', stt_engine='whisper',
                                          stt_language=SimpleNamespace(idiom='pt_BR'))
        results.record_result({'status': 'completed', 'command': 'voices', 'output': '2. Old name'})
        with patch.dict('sys.modules', {shared.__name__: shared, configs.__name__: configs}):
            state = results.current_state('voices')
        self.assertEqual(state['tts']['voices'][2], {'index': 2, 'name': 'Current voice'})
        self.assertEqual(state['tts']['index_base'], 0)
        self.assertEqual(state['stt']['language'], 'pt_BR')


class StructuredVoiceTests(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).parents[3] / 'main/askai/core/commander/commands/tts_stt_cmd.py'
        tree = ast.parse(source.read_text())
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef))
        names = {'voice_list', 'voice_set', 'voice_play', '_resolve_voice'}
        cls.bases = []
        cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.speech = Mock(spec=['model_name', 'voice', 'voices', 'select_voice', 'synthesize'])
        self.speech.model_name, self.speech.voice = 'eleven_v4', 'Voice 0'
        self.speech.voices.return_value = [f'Voice {index}' for index in range(15)]
        self.speech.select_voice.side_effect = lambda voice: setattr(self.speech, 'voice', voice)
        self.scope = {'shared': SimpleNamespace(speech=SimpleNamespace(tts=self.speech)), 'text_formatter': Mock()}
        module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
        exec(compile(module, str(source), 'exec'), self.scope)
        self.commands = self.scope['TtsSttCmd']

    def test_voice_twelve_can_be_listed_and_selected_without_asking_its_name(self):
        catalogue = self.commands.voice_list()
        self.assertEqual(catalogue['voices'][12], {'index': 12, 'name': 'Voice 12'})
        result = self.commands.voice_set('12')
        self.assertEqual(result['selected_voice'], 'Voice 12')
        self.speech.select_voice.assert_called_once_with('Voice 12')

    def test_out_of_range_index_has_a_structured_failure_and_never_selects(self):
        result = self.commands.voice_set('99')
        self.assertEqual(result['status'], 'failed')
        self.speech.select_voice.assert_not_called()

    def test_voice_provider_failure_is_not_misreported_as_success(self):
        self.speech.select_voice.side_effect = RuntimeError('Quota exhausted')
        with self.assertRaisesRegex(RuntimeError, 'Quota exhausted'):
            self.commands.voice_set('12')
