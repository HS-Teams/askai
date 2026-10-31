"""Parse slash commands without losing quoted argument boundaries."""

import shlex


def command_args(command) -> list[str]:
    return [command.group(1), *shlex.split(command.group(2) or "")]
