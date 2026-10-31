"""Context capacity reported by the agent runtime and its model catalogue."""

import json
import os
from pathlib import Path


def positive_integer(value) -> bool:
    return type(value) is int and value > 0


def codex_context_window(model: str | None) -> int | None:
    if not model:
        return None
    home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
    try:
        catalogue = json.loads((home / 'models_cache.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(catalogue, dict) or not isinstance(catalogue.get('models'), list):
        return None
    for entry in catalogue['models']:
        if not isinstance(entry, dict) or entry.get('slug') != model:
            continue
        window = entry.get('context_window')
        if not positive_integer(window):
            return None
        percent = entry.get('effective_context_window_percent')
        if percent is not None:
            if not positive_integer(percent) or percent > 100:
                return None
            window = window * percent // 100
        return window if window > 0 else None
    return None
