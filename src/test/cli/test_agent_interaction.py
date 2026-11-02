import unittest
from unittest.mock import Mock, patch
from askai.cli.agent_interaction import AgentInteraction


class InteractionTests(unittest.TestCase):
    def setUp(self):
        tty = patch("askai.cli.agent_interaction.sys.stdin.isatty", return_value=True)
        tty.start()
        self.addCleanup(tty.stop)
        self.show = Mock()

    def test_approval_uses_project_reader_and_human_message(self):
        read = Mock(return_value="1")
        response = AgentInteraction(read, self.show)(
            "item/commandExecution/requestApproval",
            {
                "reason": "Posso reproduzir a música?",
                "command": "afplay song.mp3",
                "threadId": "internal-id",
                "availableDecisions": ["accept", "cancel"],
            },
        )
        self.assertEqual(response, {"decision": "accept"})
        read.assert_called_once()
        rendered = self.show.call_args.args[0]
        self.assertIn("Posso reproduzir", rendered)
        self.assertNotIn("internal-id", rendered)
        self.assertNotIn("availableDecisions", rendered)

    def test_negative_voice_answer_uses_supported_cancel(self):
        response = AgentInteraction(Mock(return_value="2"), self.show)(
            "item/commandExecution/requestApproval",
            {"availableDecisions": ["accept", "cancel"]},
        )
        self.assertEqual(response, {"decision": "cancel"})

    def test_ambiguous_answer_does_not_authorize(self):
        read = Mock(side_effect=["x", "2"])
        response = AgentInteraction(read, self.show)("approval", {})
        self.assertEqual(response, {"decision": "decline"})
        self.assertEqual(read.call_count, 2)

    def test_questions_use_project_input(self):
        read = Mock(return_value="Downloads")
        response = AgentInteraction(read, self.show)(
            "item/tool/requestUserInput",
            {"questions": [{"id": "folder", "question": "Qual pasta?"}]},
        )
        self.assertEqual(response, {"answers": {"folder": {"answers": ["Downloads"]}}})

    def test_secret_does_not_use_voice_or_visible_input(self):
        read = Mock()
        secret = Mock(return_value="secret")
        AgentInteraction(read, self.show, secret)(
            "item/tool/requestUserInput",
            {"questions": [{"id": "key", "question": "Chave?", "isSecret": True}]},
        )
        read.assert_not_called()
        secret.assert_called_once()

    def test_local_input_form_does_not_ask_permission_before_names(self):
        from askai.core.agents.elicitation import INPUT_FORM_METHOD
        confirm = Mock(side_effect=AssertionError('No confirmation before data entry'))
        response = AgentInteraction(Mock(return_value='Hugo'), self.show, confirm=confirm)(
            INPUT_FORM_METHOD, {'mode': 'form', 'message': 'Name this face', 'requestedSchema': {
                'type': 'object', 'properties': {'name': {'type': 'string'}},
            }},
        )
        self.assertEqual(response, {'action': 'accept', 'content': {'name': 'Hugo'}})
        confirm.assert_not_called()

    def test_desktop_mcp_grants_reach_reusable_confirmation(self):
        confirm = Mock(return_value=True)
        params = {'serverName': 'askai_desktop', 'mode': 'form', 'message': 'Play music?',
                  'requestedSchema': {'type': 'object', 'properties': {},
                                      'x-askai-grants': ['askai.grants.media.play.local']}}
        response = AgentInteraction(Mock(), self.show, confirm=confirm)(
            'mcpServer/elicitation/request', params)
        self.assertEqual(response['action'], 'accept')
        self.assertEqual(confirm.call_args.kwargs['grants'], ['askai.grants.media.play.local'])
