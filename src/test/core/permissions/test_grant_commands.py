import ast
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch
from askai.core.commander.commands.grants_cmd import GrantsCmd
from askai.core.permissions.grants import GRANTS, PREFIX


class GrantCommandTests(unittest.TestCase):
    def setUp(self):
        self.settings = Mock()
        self.patch = patch.dict(sys.modules, {
            'askai.core.commander.commands.settings_cmd': Mock(SettingsCmd=self.settings),
        })
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_set_get_list_use_existing_settings_commands(self):
        GrantsCmd.run('set', 'media.play.local', 'allow')
        self.settings.set.assert_called_once_with(PREFIX + 'media.play.local', 'allow')
        GrantsCmd.run('get', PREFIX + 'camera.capture.local')
        self.settings.get.assert_called_once_with(PREFIX + 'camera.capture.local')
        GrantsCmd.run('list', 'camera')
        self.settings.list.assert_called_once_with(PREFIX + 'camera')

    def test_reset_defaults_to_ask_without_resetting_other_settings(self):
        GrantsCmd.run('reset')
        self.assertEqual(self.settings.set.call_count, len(GRANTS))
        for call in self.settings.set.call_args_list:
            self.assertTrue(call.args[0].startswith(PREFIX))
            self.assertEqual(call.args[1], 'ask')
        self.settings.reset.assert_not_called()

    def test_invalid_key_or_value_does_not_write(self):
        for name, value in [('media.*.local', 'allow'), ('media.play.local', 'yes')]:
            with self.assertRaises(ValueError):
                GrantsCmd.run('set', name, value)
        self.settings.set.assert_not_called()

    def test_direct_settings_path_also_validates_grants(self):
        source = Path(__file__).parents[3] / 'main/askai/core/askai_settings.py'
        tree = ast.parse(source.read_text())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'AskAiSettings')
        method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == '__setitem__')
        scope = {'Any': object}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(source), 'exec'), scope)
        settings = Mock()
        with self.assertRaises(ValueError):
            scope['__setitem__'](settings, PREFIX + 'media.play.local', 'yes')
        settings._settings.put.assert_not_called()
        scope['__setitem__'](settings, PREFIX + 'media.play.local', 'allow')
        settings._settings.put.assert_called_once_with(PREFIX + 'media.play.local', 'askai', 'allow')
