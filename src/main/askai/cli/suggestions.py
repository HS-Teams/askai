"""Shared completion policy for CLI and TUI input."""


def input_suggestion(value, entries, case_sensitive=True):
    compare = (lambda text: text) if case_sensitive else str.casefold
    prefix = compare(value)
    command_name = value.startswith('/') and not any(char.isspace() for char in value)
    candidates = [entry.split(maxsplit=1)[0] if command_name and entry else entry for entry in entries]
    if command_name:
        exact = next((entry for entry in candidates if compare(entry) == prefix), None)
        if exact is not None:
            return exact
    for candidate in candidates:
        if compare(candidate).startswith(prefix):
            return candidate
    return None
