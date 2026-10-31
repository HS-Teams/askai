import unittest
from unittest.mock import Mock, patch
from askai.cli.agent_interaction import AgentInteraction
from askai.core.agents.elicitation import ELICITATION_METHOD, decode_form
from askai.core.agents.codex import CodexBackend
from jsonschema import ValidationError


class ElicitationTests(unittest.TestCase):
    def invoke(self, params, answers=(), accepted=True):
        with patch("sys.stdin.isatty", return_value=True):
            return AgentInteraction(
                Mock(side_effect=answers), Mock(), confirm=Mock(return_value=accepted)
            )(ELICITATION_METHOD, params)

    def test_empty_form_is_confirmation(self):
        params = {
            "mode": "form",
            "message": "Autorizar?",
            "requestedSchema": {"type": "object", "properties": {}},
        }
        self.assertEqual(self.invoke(params), {"action": "accept", "content": {}})
        self.assertEqual(self.invoke(params, accepted=False), {"action": "decline"})

    def test_form_returns_typed_fields(self):
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "minimum": 1},
                "allow": {"type": "boolean"},
            },
            "required": ["count", "allow"],
        }
        result = self.invoke({"mode": "form", "requestedSchema": schema}, ["2", "Sim"])
        self.assertEqual(result["content"], {"count": 2, "allow": True})
        with self.assertRaises(ValidationError):
            decode_form(schema, {"count": "0", "allow": "sim"})

    def test_url_requires_explicit_confirmation(self):
        result = self.invoke(
            {
                "mode": "url",
                "url": "https://example.com/authorize",
                "message": "Continue",
            },
            accepted=False,
        )
        self.assertEqual(result, {"action": "decline"})

    def test_cancelling_form_does_not_accept(self):
        result = self.invoke(
            {
                "mode": "form",
                "requestedSchema": {"properties": {"name": {"type": "string"}}},
            },
            ["/cancelar"],
        )
        self.assertEqual(result, {"action": "cancel"})

    def test_transport_returns_mcp_response_not_approval_response(self):
        transport = Mock()
        params = {
            "mode": "form",
            "requestedSchema": {"type": "object", "properties": {}},
        }
        response = {"action": "accept", "content": {}}
        CodexBackend._respond(
            transport,
            {"id": 7, "method": ELICITATION_METHOD, "params": params},
            Mock(return_value=response),
        )
        transport.send.assert_called_once_with({"id": 7, "result": response})

    def test_uncorrelated_turn_elicitation_is_delivered(self):
        from threading import Event
        transport = Mock()
        transport.receive.side_effect = [
            {'id': 5, 'method': ELICITATION_METHOD, 'params': {
                'threadId': 's', 'turnId': None, 'mode': 'form',
                'requestedSchema': {'type': 'object', 'properties': {}}}},
            {'method': 'item/completed', 'params': {'item': {
                'type': 'agentMessage', 'phase': 'final_answer', 'id': 'a', 'text': 'Done'}}},
            {'method': 'turn/completed', 'params': {'turn': {'id': 't', 'status': 'completed'}}},
        ]
        interact = Mock(return_value={'action': 'decline'})
        result = CodexBackend()._consume(transport, 's', 't', Mock(), interact, Event())
        self.assertEqual(result.answer, 'Done')
        interact.assert_called_once()
        transport.send.assert_called_once_with({'id': 5, 'result': {'action': 'decline'}})
