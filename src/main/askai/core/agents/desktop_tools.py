"""Process-scoped Codex MCP configuration; never edits the user's Codex config."""

import json
from pathlib import Path
import sys


def app_server_command(executable: str, read_only: bool) -> list[str]:
    config = {
        "mcp_servers.askai_desktop.command": sys.executable,
        "mcp_servers.askai_desktop.args": ["-m", "askai.mcp_server"],
        "mcp_servers.askai_desktop.env.PYTHONPATH": str(
            Path(__file__).resolve().parents[3]
        ),
        "mcp_servers.askai_desktop.enabled": not read_only,
    }
    command = [executable, "app-server"]
    for key, value in config.items():
        command.extend(["-c", f"{key}={json.dumps(value)}"])
    return command
