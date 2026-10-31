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

    def test_only_grant_protected_tools_skip_native_duplicate_prompt(self):
        command = app_server_command('codex', False, '/tmp/test-scope')
        for tool in ('open_path', 'open_application', 'play_music', 'control_music', 'open_camera'):
            self.assertIn(f'mcp_servers.askai_desktop.tools.{tool}.approval_mode="approve"', command)
        self.assertNotIn('approval_policy="never"', command)
        self.assertNotIn('mcp_servers.askai_desktop.default_tools_approval_mode="approve"', command)
        self.assertIn('mcp_servers.askai_desktop.env.ASKAI_ACTION_SCOPE_FILE="/tmp/test-scope"', command)
