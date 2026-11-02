import ast
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace as NS
import unittest
from unittest.mock import Mock, patch
from askai.core.speech.narration import parse_narration


class DictationReplyTests(unittest.TestCase):
    def test_saved_notices_precede_speakable_final_answer(self):
        path = Path(__file__).resolve().parents[3] / 'main/askai/core/commander/commands/tts_stt_cmd.py'
        tree = ast.parse(path.read_text())
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == 'dictate')
        node.decorator_list = []
        order = []
        formatter = Mock()
        formatter.commander_print.side_effect = lambda text: order.append(('notice', text))
        events = Mock()
        events.reply.emit.side_effect = lambda **kwargs: order.append(('reply', kwargs['reply']))
        refined = 'Joãozinho gostava de futebol.'
        recorder = Mock()
        recorder.listen.return_value = (None, 'original')
        player = Mock()
        scope = dict(__file__=str(path), Path=Path, recorder=recorder, text_formatter=formatter,
                     configs=NS(is_keep_context=False, agent='codex'), shared=Mock())
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), scope)
        modules = {
            'askai.core.component.multimedia.audio_player': NS(player=player),
            'askai.core.askai_messages': NS(msg=NS(t=lambda text: text, dictating=lambda: 'Dictating')),
            'askai.core.askai_prompt': NS(prompt=Mock()),
            'askai.core.askai_events': NS(events=events),
            'askai.core.support.inference': NS(complete=Mock(return_value='{"final_text":"' + refined + '"}')),
            'askai.core.speech.dictation_memory': NS(register=Mock()),
            'askai.core.support.persistent_memory': NS(PersistentMemory=Mock()),
            'askai.core.support.app_paths': NS(askai_data_dir=Mock()),
            'askai.cli.dictation_input': NS(finish_requested=Mock()),
        }
        with TemporaryDirectory() as directory, patch.dict('sys.modules', modules):
            destination = Path(directory) / 'dictation.txt'
            scope['dictate'](str(destination))
            self.assertEqual(destination.read_text(), refined)
            sound = player.play_audio_file.call_args.args[0]
            self.assertEqual(sound.name, 'dictate-start.mp3')
            self.assertTrue(sound.is_file())
            recorder.listen.call_args.kwargs["on_captured"]()
            end_sound = player.play_audio_file.call_args.args[0]
            self.assertEqual(end_sound.name, "dictate-end.mp3")
            self.assertTrue(end_sound.is_file())
        self.assertEqual([kind for kind, _ in order], ['notice', 'notice', 'reply'])
        reply = order[-1][1]
        self.assertTrue(reply.is_final)
        self.assertTrue(reply.is_speakable)
        self.assertEqual(parse_narration(reply.message, required=True).spoken, refined)
