import unittest
from askai.core.agents.desktop_tools import app_server_command


class DesktopToolConfigTests(unittest.TestCase):
    def test_tools_enabled_for_execution_disabled_for_reviews(self):
        self.assertIn(
            "mcp_servers.askai_desktop.enabled=true", app_server_command("codex", False)
        )
        self.assertIn(
            "mcp_servers.askai_desktop.enabled=false", app_server_command("codex", True)
        )
        self.assertIn(
            'mcp_servers.askai_desktop.args=["-m", "askai.mcp_server"]',
            app_server_command("codex", False),
        )
