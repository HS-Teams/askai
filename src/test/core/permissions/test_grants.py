import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from askai.core.permissions.grants import GrantPolicy, GrantDenied, PREFIX, grant_key, validate_setting, read_grant


class GrantTests(unittest.TestCase):
    def test_saving_never_and_declining_returns_false_without_exception(self):
        read = Mock(side_effect=['ask', 'never'])
        policy = GrantPolicy(read)
        response = Mock(return_value={'action': 'decline'})
        self.assertFalse(policy.authorize(['camera.capture.local'], 'Capture?', response))
        with self.assertRaises(GrantDenied):
            policy.pending(['camera.capture.local'])


    def test_allow_skips_confirmation_and_ask_is_per_action(self):
        confirm = Mock(return_value={'action': 'accept', 'content': {}})
        policy = GrantPolicy(lambda key: 'allow')
        self.assertTrue(policy.authorize(['camera.capture.local'], 'Capture?', confirm))
        confirm.assert_not_called()
        policy = GrantPolicy(lambda key: 'ask')
        for _ in range(2):
            self.assertTrue(policy.authorize(['camera.capture.local', 'vision.share.agent'], 'Capture and share?', confirm))
        self.assertEqual(confirm.call_count, 2)

    def test_bundle_deny_blocks_before_any_prompt_or_capture(self):
        confirm = Mock()
        policy = GrantPolicy(lambda key: 'deny' if key.endswith('vision.share.agent') else 'ask')
        with self.assertRaises(GrantDenied):
            policy.authorize(['camera.capture.local', 'vision.share.agent'], 'Capture?', confirm)
        confirm.assert_not_called()

    def test_invalid_values_unknown_names_and_wildcards_never_allow(self):
        for value in ('yes', '', None, True):
            with self.assertRaises(GrantDenied):
                GrantPolicy(lambda key: value).pending(['camera.capture.local'])
            with self.assertRaises(ValueError):
                validate_setting('camera.capture.local', value)
        for name in ('camera.*.local', 'camera.capture', 'unknown.foo.local'):
            with self.assertRaises(ValueError):
                grant_key(name)

    def test_decline_is_not_persisted_and_later_deny_takes_effect(self):
        values = {PREFIX + 'media.play.local': 'ask'}
        policy = GrantPolicy(values.get)
        confirm = Mock(return_value={'action': 'decline'})
        self.assertFalse(policy.authorize(['media.play.local'], 'Play?', confirm))
        values[PREFIX + 'media.play.local'] = 'allow'
        self.assertTrue(policy.authorize(['media.play.local'], 'Play?', confirm))
        values[PREFIX + 'media.play.local'] = 'deny'
        with self.assertRaises(GrantDenied):
            policy.authorize(['media.play.local'], 'Play?', confirm)
        confirm.assert_called_once()

    def test_read_only_scope_blocks_even_persistent_allow(self):
        with TemporaryDirectory() as directory:
            scope = Path(directory) / 'scope'
            with patch.dict(os.environ, {'ASKAI_ACTION_SCOPE_FILE': str(scope)}):
                policy = GrantPolicy(lambda key: 'allow')
                with self.assertRaises(GrantDenied):
                    policy.pending(['media.play.local'])
                scope.write_text('deny')
                with self.assertRaises(GrantDenied):
                    policy.pending(['media.play.local'])
                scope.write_text('allow')
                self.assertEqual(policy.pending(['media.play.local']), [])

    def test_live_settings_read_never_creates_another_database(self):
        with TemporaryDirectory() as directory, patch('askai.core.permissions.grants.askai_data_dir', return_value=Path(directory)):
            self.assertEqual(read_grant(PREFIX + 'media.play.local'), 'ask')
            self.assertEqual(list(Path(directory).iterdir()), [])
            path = Path(directory) / 'askai.db'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE SETTINGS (name TEXT PRIMARY KEY, value TEXT)')
                db.execute('INSERT INTO SETTINGS VALUES (?,?)', (PREFIX + 'media.play.local', 'allow'))
            self.assertEqual(read_grant(PREFIX + 'media.play.local'), 'allow')
            with sqlite3.connect(path) as db:
                db.execute('UPDATE SETTINGS SET value=?', ('deny',))
            self.assertEqual(read_grant(PREFIX + 'media.play.local'), 'deny')
