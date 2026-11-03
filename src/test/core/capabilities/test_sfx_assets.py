"""The shared audio player resolves every relocated effect without opening a device."""
import ast
from pathlib import Path
from types import SimpleNamespace as NS
from typing import Literal
import unittest
from unittest.mock import Mock, patch
from hspylib.core.preconditions import check_argument
from hspylib.core.tools.commons import file_is_not_empty
from hspylib.core.tools.text_tools import ensure_endswith


class SoundAssetTests(unittest.TestCase):
    def test_shared_player_resolves_gestures_ui_voices_and_intros(self):
        root = Path(__file__).resolve().parents[3] / 'main/askai'
        source = root / 'core/component/multimedia/audio_player.py'
        tree = ast.parse(source.read_text())
        player = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'AudioPlayer')
        player.keywords = []
        player.body = [node for node in player.body if
                       (isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SFX_DIR' for t in node.targets))
                       or (isinstance(node, ast.FunctionDef) and node.name == 'play_sfx')]
        scope = dict(classpath=NS(resource_path=root / 'resources'), Literal=Literal,
                     check_argument=check_argument, file_is_not_empty=file_is_not_empty,
                     ensure_endswith=ensure_endswith)
        exec(compile(ast.Module(body=[player], type_ignores=[]), str(source), 'exec'), scope)
        audio_player = scope['AudioPlayer']
        audio_player.play_audio_file = Mock(return_value=True)
        sounds = root / 'resources/sfx'
        self.assertEqual(Path(audio_player.SFX_DIR), sounds)
        self.assertFalse((root / 'resources/sound-fx').exists())
        for category in ('gestures', 'ui', 'voices', 'intros'):
            assets = [path for path in (sounds / category).iterdir() if path.suffix in ('.mp3', '.ogg')]
            self.assertTrue(assets, category)
            for asset in assets:
                with self.subTest(asset=asset.name):
                    relative = asset.relative_to(sounds)
                    with patch('askai.core.speech.effects.play', return_value=True) as play:
                        self.assertTrue(audio_player.play_sfx(str(relative.with_suffix('')), file_ext=asset.suffix))
                        play.assert_called_once_with(str(asset), loop=None)
                    audio_player.play_audio_file.assert_not_called()
