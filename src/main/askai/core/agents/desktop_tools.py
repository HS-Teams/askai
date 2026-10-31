"""Process-scoped Codex MCP configuration; never edits the user's Codex config."""

import json
from pathlib import Path
import sys
from askai.core.support.app_paths import askai_data_dir


def app_server_command(executable: str, read_only: bool, action_scope: str | None = None) -> list[str]:
    config = {
        "mcp_servers.askai_desktop.command": sys.executable,
        "mcp_servers.askai_desktop.args": ["-m", "askai.mcp_server"],
        "mcp_servers.askai_desktop.env.PYTHONPATH": str(
            Path(__file__).resolve().parents[3]
        ),
        "mcp_servers.askai_desktop.env.ASKAI_DIR": str(askai_data_dir()),
        "mcp_servers.askai_desktop.enabled": not read_only,
    }
    if action_scope:
        config["mcp_servers.askai_desktop.env.ASKAI_ACTION_SCOPE_FILE"] = action_scope
    # These tools enforce core grants themselves, including ask/deny.
    for tool in ("open_path", "open_application", "play_music", "control_music", "open_camera"):
        config[f"mcp_servers.askai_desktop.tools.{tool}.approval_mode"] = "approve"
    command = [executable, "app-server"]
    for key, value in config.items():
        command.extend(["-c", f"{key}={json.dumps(value)}"])
    return command
