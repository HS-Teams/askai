import unittest
from unittest.mock import Mock, patch

from askai.core.agents.codex import CodexBackend
from askai.core.agents.elicitation import ELICITATION_METHOD
from askai.core.permissions.grants import GrantPolicy


class ComputerUseTests(unittest.TestCase):
    def test_same_app_consent_ignores_per_call_metadata_and_ids(self):
        consent = {}
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        with patch('askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: 'ask')):
            for number, mode in enumerate(('form', 'openai/form', 'openaiForm')):
                request = self.request(mode=mode, requestId=number, itemId=str(number),
                                       _meta={'progressToken': number, 'traceId': str(number)})
                CodexBackend._respond(Mock(), request, interact, consent)
        interact.assert_called_once()
        self.assertEqual(len(consent), 1)

    def test_changed_explicit_permission_scope_requires_new_consent(self):
        consent = {}
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        with patch('askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: 'ask')):
            CodexBackend._respond(Mock(), self.request(permissions=['read']), interact, consent)
            CodexBackend._respond(Mock(), self.request(permissions=['read', 'write']), interact, consent)
        self.assertEqual(interact.call_count, 2)

    def test_revocation_discards_cached_acceptance(self):
        consent = {}
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        for value in ('ask', 'deny', 'ask'):
            with patch('askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: value)):
                CodexBackend._respond(Mock(), self.request(), interact, consent)
        self.assertEqual(interact.call_count, 2)


    def test_rpc_identifiers_do_not_repeat_app_consent_but_metadata_does(self):
        consent = {}
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        with patch('askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: 'ask')):
            for identifier in ('one', 'two'):
                CodexBackend._respond(Mock(), self.request(requestId=identifier, threadId='s', turnId='t'),
                                      interact, consent)
            interact.assert_called_once()
            CodexBackend._respond(Mock(), self.request(_meta={'scope': 'different'}), interact, consent)
            self.assertEqual(interact.call_count, 2)


    def test_same_consent_is_reused_only_in_current_turn_and_rechecks_denials(self):
        consent = {}
        policy = GrantPolicy(lambda key: 'ask')
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        with patch('askai.core.permissions.computer_use.grants', policy):
            for _ in range(3):
                CodexBackend._respond(Mock(), self.request(), interact, consent)
            interact.assert_called_once()
            CodexBackend._respond(Mock(), self.request(message='Allow another app?'), interact, consent)
            self.assertEqual(interact.call_count, 2)
            CodexBackend._respond(Mock(), self.request(), interact, {})
            self.assertEqual(interact.call_count, 3)
        with patch('askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: 'deny')):
            transport = Mock()
            CodexBackend._respond(transport, self.request(), interact, consent)
        self.assertEqual(transport.send.call_args.args[0]['result'], {'action': 'decline'})


    def request(self, **changes):
        params = {'serverName': 'cua_repl', 'mode': 'form',
                  'message': 'Allow computer use for Reminders?',
                  'requestedSchema': {'type': 'object', 'properties': {}}}
        params.update(changes)
        return {'id': 7, 'method': ELICITATION_METHOD, 'params': params}

    def test_allow_and_deny_skip_prompt(self):
        for value, expected in [('allow', {'action': 'accept', 'content': {}}),
                                ('deny', {'action': 'decline'}),
                                ('never', {'action': 'decline'})]:
            with self.subTest(value=value), patch(
                    'askai.core.permissions.computer_use.grants', GrantPolicy(lambda key: value)):
                transport, interact = Mock(), Mock()
                CodexBackend._respond(transport, self.request(), interact)
                interact.assert_not_called()
                transport.send.assert_called_once_with({'id': 7, 'result': expected})

    def test_ask_labels_grant_and_rechecks_live_setting(self):
        read = Mock(side_effect=['ask', 'ask', 'allow', 'deny'])
        interact = Mock(return_value={'action': 'accept', 'content': {}})
        transport = Mock()
        with patch('askai.core.permissions.computer_use.grants', GrantPolicy(read)):
            CodexBackend._respond(transport, self.request(), interact)
            CodexBackend._respond(transport, self.request(), interact)
        interact.assert_called_once()
        params = interact.call_args.args[1]
        self.assertTrue(params['message'].startswith('Use the computer'))
        self.assertEqual(params['askaiGrants'], ['askai.grants.computer.use'])
        self.assertEqual(transport.send.call_args.args[0]['result'], {'action': 'decline'})

    def test_other_servers_url_and_input_forms_keep_normal_interaction(self):
        requests = [self.request(serverName='another_server'),
                    self.request(mode='url', url='https://example.com'),
                    self.request(requestedSchema={'type': 'object', 'properties': {'name': {'type': 'string'}}})]
        for request in requests:
            with self.subTest(params=request['params']):
                interact = Mock(return_value={'action': 'decline'})
                with patch('askai.core.permissions.computer_use.grants') as policy:
                    CodexBackend._respond(Mock(), request, interact)
                policy.authorize.assert_not_called()
                interact.assert_called_once_with(ELICITATION_METHOD, request['params'])
