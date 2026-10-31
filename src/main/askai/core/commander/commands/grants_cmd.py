"""User-owned grant management through the existing settings commands."""
from askai.core.permissions.grants import GRANTS, PREFIX, grant_key, validate_setting


class GrantsCmd:
    @staticmethod
    def run(operation, name='', value=''):
        from askai.core.commander.commands.settings_cmd import SettingsCmd
        if operation == 'list':
            SettingsCmd.list(PREFIX + name.removeprefix(PREFIX))
        elif operation == 'get':
            SettingsCmd.get(grant_key(name))
        elif operation == 'set':
            key = grant_key(name)
            SettingsCmd.set(key, validate_setting(key, value))
        elif operation == 'reset':
            keys = [grant_key(name)] if name else [PREFIX + grant for grant in GRANTS]
            for key in keys:
                SettingsCmd.set(key, 'ask', announce=False)
            SettingsCmd.list(PREFIX + name.removeprefix(PREFIX))
