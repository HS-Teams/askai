"""Exercise command bodies without initializing microphones, keychain or databases."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).parents[3] / 'main/askai'


def load_definition(path, name, namespace):
    tree = ast.parse((ROOT / path).read_text())
    node = next(node for node in tree.body if getattr(node, 'name', None) == name)
    node.decorator_list = []
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(module, str(path), 'exec'), namespace)
    return namespace[name]


class SettingCommandTests(unittest.TestCase):
    def setUp(self):
        self.store = MagicMock()
        self.output = MagicMock()
        self.namespace = dict(
            ABC=object, Any=object, Optional=__import__('typing').Optional,
            SettingsEntry=object, settings=self.store, cli_output=self.output,
        )
        self.setter = load_definition(
            'core/commander/commands/settings_cmd.py', 'SettingsCmd', self.namespace
        )

    def test_toggles_use_setting_setter_in_both_directions(self):
        for command, prop, key in [
            ('speak', 'is_speak', 'askai.speak.enabled'),
            ('debug', 'is_debug', 'askai.debug.enabled'),
            ('assistive', 'is_assistive', 'askai.router.assistive.enabled'),
        ]:
            for enabled in (False, True):
                with self.subTest(command=command, enabled=enabled):
                    self.store.reset_mock()
                    namespace = dict(SettingsCmd=self.setter, configs=SimpleNamespace(**{prop: enabled}),
                                     cli_output=self.output, _format_toggle=str)
                    callback = load_definition('core/commander/commander.py', command, namespace)
                    callback()
                    self.store.put.assert_called_once_with(key, not enabled)

    def test_enable_commands_persist_true_and_false(self):
        for command, prop, key in [('cache', 'is_cache', 'askai.cache.enabled'),
                                   ('rag', 'is_rag', 'askai.rag.enabled')]:
            for value in ('0', '1'):
                with self.subTest(command=command, value=value):
                    self.store.reset_mock()
                    namespace = dict(SettingsCmd=self.setter, configs=SimpleNamespace(**{prop: value == '1'}),
                                     cli_output=self.output, to_bool=lambda value: value == '1')
                    callback = load_definition('core/commander/commander.py', command, namespace)
                    callback('enable', (value,))
                    self.store.put.assert_called_once_with(key, value == '1')

    def test_unknown_setting_is_not_written(self):
        self.store.__getitem__.return_value = None
        self.setter.set('unknown', True)
        self.store.put.assert_not_called()

    def test_mute_persists_only_effect_setting_and_updates_live_players(self):
        for muted in (False, True):
            with self.subTest(muted=muted), patch('askai.core.speech.effects.set_muted') as local, patch(
                    'askai.gestures.background.set_sfx_muted') as worker:
                self.store.reset_mock()
                self.store.get_bool.return_value = not muted
                config = SimpleNamespace(is_sfx_muted=muted, is_speak=True)
                callback = load_definition('core/commander/commander.py', 'mute', dict(
                    SettingsCmd=self.setter, configs=config, cli_output=self.output, _format_toggle=str))
                callback()
                self.store.put.assert_called_once_with('askai.sfx.muted', not muted)
                local.assert_called_once_with(not muted)
                worker.assert_called_once_with(not muted)
                self.assertTrue(config.is_speak)

    def test_startup_adds_mute_default_without_resetting_saved_preferences(self):
        tree = ast.parse((ROOT / 'core/askai_settings.py').read_text())
        node = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == '__init__')
        for saved in (None, False, True):
            with self.subTest(saved=saved):
                values = {'askai.settings.version.id': '0.4.3', 'askai.speak.enabled': True}
                if saved is not None:
                    values['askai.sfx.muted'] = saved
                instance = SimpleNamespace(__RESOURCE_DIR='unused', __ACTUAL_VERSION='0.4.3',
                                           get=lambda key, default='': values.get(key, default),
                                           put=lambda key, value: values.__setitem__(key, value), defaults=MagicMock())
                namespace = dict(SettingsConfig=MagicMock(), Settings=lambda _: SimpleNamespace(count=lambda: 1))
                exec(compile(ast.Module(body=[node], type_ignores=[]), '<settings-init>', 'exec'), namespace)
                namespace['__init__'](instance)
                self.assertEqual(values['askai.sfx.muted'], saved if saved is not None else False)
                self.assertTrue(values['askai.speak.enabled'])
                instance.defaults.assert_not_called()

    def test_setting_confirmation_remains_default_but_can_be_suppressed(self):
        self.setter.set('askai.speak.enabled', True)
        self.output.render_command.assert_called_once()
        self.output.reset_mock()
        self.setter.set('askai.speak.enabled', False, announce=False)
        self.output.render_command.assert_not_called()

    def test_cli_and_tui_preserve_saved_flags_and_allow_explicit_enable(self):
        tree = ast.parse((ROOT / '__main__.py').read_text())
        constructors = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)
                        and node.func.attr in ('AskAiCli', 'AskAiApp')]
        self.assertEqual(len(constructors), 2)
        for call in constructors:
            for index, flag in enumerate(('speak', 'debug')):
                for saved, supplied in ((True, False), (False, False), (False, True), (True, True)):
                    with self.subTest(view=call.func.attr, flag=flag, saved=saved, supplied=supplied):
                        namespace = dict(self=SimpleNamespace(_get_argument=lambda name: supplied),
                                         configs=SimpleNamespace(**{f'is_{flag}': saved}), to_bool=bool)
                        value = eval(compile(ast.Expression(call.args[index]), '<startup>', 'eval'), namespace)
                        self.assertEqual(value, saved or supplied)

    def test_history_commands_route_dates_and_persist_resume_setting(self):
        import click
        history = MagicMock()
        callback = load_definition('core/commander/commander.py', 'history', dict(
            HistoryCmd=history, SettingsCmd=self.setter, click=click,
        ))
        callback('list')
        history.history_list.assert_called_once_with(None)
        callback('list', '2026-10-31')
        history.history_list.assert_called_with('2026-10-31')
        for value in ('0', '1'):
            callback('enable', value)
            self.store.put.assert_called_with('askai.context.keep.conversation', value == '1')
        callback('forget')
        history.history_forget.assert_called_once_with()
        self.store.reset_mock()
        history.reset_mock()
        for operation, value in [('list', 'invalid'), ('enable', None), ('enable', 'yes'), ('forget', 'all')]:
            with self.subTest(operation=operation, value=value), self.assertRaises(click.BadParameter):
                callback(operation, value)
        self.store.put.assert_not_called()
        history.history_list.assert_not_called()
        history.history_forget.assert_not_called()
