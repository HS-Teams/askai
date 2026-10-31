import unittest
from pathlib import Path
from unittest.mock import patch
from askai.core.support.app_paths import askai_data_dir
from askai.core.agents.desktop_tools import app_server_command


class AppPathTests(unittest.TestCase):
    def test_exported_directory_is_not_nested_again(self):
        with patch.dict('os.environ', {'ASKAI_DIR': '/data/askai'}, clear=True):
            self.assertEqual(askai_data_dir(), Path('/data/askai'))
            self.assertIn('mcp_servers.askai_desktop.env.ASKAI_DIR="/data/askai"', app_server_command('codex', False))

    def test_hhs_directory_and_default(self):
        with patch.dict('os.environ', {'HHS_DIR': '/data/hhs'}, clear=True):
            self.assertEqual(askai_data_dir(), Path('/data/hhs/askai'))
        with patch.dict('os.environ', {}, clear=True), patch('pathlib.Path.home', return_value=Path('/home/test')):
            self.assertEqual(askai_data_dir(), Path('/home/test/.config/hhs/askai'))
