import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch, call
from askai.core.speech.narration import parse_narration
from askai.core.speech.capture import CaptureCancelled


class DictationReplyTests(unittest.TestCase):
    def test_empty_or_failed_dictation_does_not_replace_clipboard(self):
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/commander/commands/tts_stt_cmd.py'
        node = next(n for n in ast.walk(ast.parse(path.read_text()))
                    if isinstance(n, ast.FunctionDef) and n.name == 'dictate')
        node.decorator_list = []
        recorder, clipboard, complete = Mock(), Mock(), Mock(side_effect=ValueError('Refinement failed'))
        scope = dict(__file__=str(path), Path=Path, recorder=recorder, cli_output=Mock())
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        modules = {
            'pyperclip': clipboard,
            'askai.core.component.multimedia.audio_player': NS(player=Mock()),
            'askai.core.askai_messages': NS(msg=NS(t=lambda text: text, dictating=lambda: 'Dictating')),
            'askai.core.askai_prompt': NS(prompt=Mock()),
            'askai.core.support.inference': NS(complete=complete),
            'askai.core.support.app_paths': NS(askai_data_dir=Mock()),
            'askai.cli.dictation_input': NS(cancel_requested=Mock()),
        }
        for original in ('', 'Original transcription', RuntimeError('Capture failed'), CaptureCancelled()):
            process = Mock(poll=Mock(return_value=None))
            with self.subTest(original=original), TemporaryDirectory() as directory, patch.dict(
                    'sys.modules', modules), patch('askai.gestures.background._process', process):
                destination = Path(directory) / 'dictation.txt'

                def capture(**kwargs):
                    process.stdin.write.assert_called_once_with('pause\n')
                    if isinstance(original, Exception):
                        raise original
                    return None, original

                recorder.listen.side_effect = capture
                if isinstance(original, CaptureCancelled):
                    scope['dictate'](str(destination))
                    self.assertFalse(destination.exists())
                    self.assertFalse(destination.with_name(destination.name + '.orig').exists())
                    scope['cli_output'].render_command.assert_called_with('Dictation cancelled.')
                elif isinstance(original, Exception):
                    with self.assertRaisesRegex(RuntimeError, 'Capture failed'):
                        scope['dictate'](str(destination))
                elif original:
                    with self.assertRaisesRegex(ValueError, 'Refinement failed'):
                        scope['dictate'](str(destination))
                    self.assertEqual(destination.with_suffix('.txt.orig').read_text(), original)
                else:
                    scope['dictate'](str(destination))
                self.assertFalse(destination.exists())
                clipboard.copy.assert_not_called()
                self.assertEqual(process.stdin.write.call_args_list, [call('pause\n'), call('resume\n')])

    def test_saved_notices_precede_speakable_final_answer(self):
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/commander/commands/tts_stt_cmd.py'
        tree = ast.parse(path.read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'dictate')
        node.decorator_list = []
        order = []
        formatter = Mock()
        formatter.render_command.side_effect = lambda text: order.append(('notice', text))
        events = Mock()
        events.reply.emit.side_effect = lambda **kwargs: order.append(('reply', kwargs['reply']))
        refined = 'Joãozinho gostava de futebol.'
        recorder = Mock()
        process = Mock(poll=Mock(return_value=None))

        def capture(**kwargs):
            self.assertEqual(kwargs['end_silence'], 2.5)
            self.assertEqual(kwargs['phrase_limit'], 0)
            self.assertIsNotNone(kwargs['cancel_requested'])
            process.stdin.write.assert_called_once_with('pause\n')
            process.stdin.flush.assert_called_once()
            return None, 'original'

        recorder.listen.side_effect = capture
        player = Mock()
        clipboard = Mock()
        clipboard.copy.side_effect = lambda text: order.append(('clipboard', text))
        scope = dict(__file__=str(path), Path=Path, recorder=recorder, cli_output=formatter,
                     configs=NS(is_keep_context=False, agent='codex'), shared=Mock())
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        modules = {
            'pyperclip': clipboard,
            'askai.core.component.multimedia.audio_player': NS(player=player),
            'askai.core.askai_messages': NS(msg=NS(t=lambda text: text, dictating=lambda: 'Dictating')),
            'askai.core.askai_prompt': NS(prompt=Mock()),
            'askai.core.askai_events': NS(events=events),
            'askai.core.support.inference': NS(complete=Mock(return_value='{"final_text":"' + refined + '"}')),
            'askai.core.speech.dictation_memory': NS(register=Mock()),
            'askai.core.support.persistent_memory': NS(PersistentMemory=Mock()),
            'askai.core.support.app_paths': NS(askai_data_dir=Mock()),
            'askai.cli.dictation_input': NS(cancel_requested=Mock()),
        }
        with TemporaryDirectory() as directory, patch.dict('sys.modules', modules), patch(
                'askai.gestures.background._process', process):
            destination = Path(directory) / 'dictation.txt'
            scope['dictate'](str(destination))
            self.assertEqual(destination.read_text(), refined)
            clipboard.copy.assert_called_once_with(refined)
            self.assertEqual(process.stdin.write.call_args_list, [call('pause\n'), call('resume\n')])
            player.play_sfx.assert_called_once_with('ui/dictate-start')
            recorder.listen.call_args.kwargs["on_captured"]()
            self.assertEqual(player.play_sfx.call_args_list,
                             [call('ui/dictate-start'), call('ui/dictate-end')])
        self.assertEqual([kind for kind, _ in order], ['notice', 'clipboard', 'notice', 'reply'])
        reply = order[-1][1]
        self.assertTrue(reply.is_final)
        self.assertTrue(reply.is_speakable)
        self.assertEqual(parse_narration(reply.message, required=True).spoken, refined)
