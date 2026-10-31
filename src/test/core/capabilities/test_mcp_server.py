import os
from pathlib import Path
import sys
import unittest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_stdio_handshake_catalog_and_action_error(self):
        main = Path(__file__).parents[3] / "main"
        parameters = StdioServerParameters(
            command=sys.executable,
            args=["-m", "askai.mcp_server"],
            env={**os.environ, "PYTHONPATH": str(main)},
        )
        async with stdio_client(parameters) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                catalog = await session.list_tools()
                self.assertEqual(
                    {tool.name for tool in catalog.tools},
                    {
                        "open_path",
                        "open_application",
                        "play_music",
                        "control_music",
                        "open_camera",
                    },
                )
                result = await session.call_tool(
                    "open_path", {"path": "relative-not-allowed"}
                )
                self.assertTrue(result.isError)
