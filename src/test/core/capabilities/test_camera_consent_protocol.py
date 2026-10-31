"""Exercise the real MCP wire and AskAI confirmation without camera hardware."""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import ElicitResult
from askai.cli.agent_interaction import AgentInteraction

# Root contract from Codex's McpElicitationSchema: titles/descriptions belong to fields.
FORM_SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['type', 'properties'],
    'properties': {
        'type': {'const': 'object'}, 'properties': {'type': 'object'},
        'required': {'type': ['array', 'null']}, '$schema': {'type': ['string', 'null']},
    },
}


class CameraConsentProtocolTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_mcp_form_accept_and_decline(self):
        script = '''
from unittest.mock import Mock
from askai.mcp_server import create_server
from askai.core.capabilities.desktop import ActionResult
capabilities = Mock()
capabilities.open_camera.return_value = ActionResult('open_camera', 'completed', 'Photo Booth')
create_server(capabilities).run(transport='stdio')
'''
        answers = iter(['1', '2'])
        seen = []
        interaction = AgentInteraction(lambda _: next(answers), Mock())

        async def elicit(context, params):
            validate(params.requestedSchema, FORM_SCHEMA)
            seen.append(params.message)
            response = interaction._elicit({
                'mode': 'form', 'serverName': 'askai_desktop',
                'message': params.message, 'requestedSchema': params.requestedSchema,
            })
            return ElicitResult(**response)

        main = Path(__file__).parents[3] / 'main'
        parameters = StdioServerParameters(command=sys.executable, args=['-c', script],
            env={**os.environ, 'PYTHONPATH': str(main)})
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer, elicitation_callback=elicit) as session:
                await session.initialize()
                accepted = await session.call_tool('open_camera', {})
                self.assertFalse(accepted.isError)
                self.assertEqual(json.loads(accepted.content[0].text)['status'], 'completed')
                denied = await session.call_tool('open_camera', {})
                self.assertEqual(json.loads(denied.content[0].text)['status'], 'cancelled')
        self.assertEqual(len(seen), 2)
