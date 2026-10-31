"""Resolve the exported AskAI data root without initializing application services."""
import os
from pathlib import Path


def askai_data_dir() -> Path:
    if directory := os.environ.get('ASKAI_DIR'):
        return Path(directory).expanduser()
    hhs = Path(os.environ.get('HHS_DIR', str(Path.home() / '.config/hhs'))).expanduser()
    return hhs / 'askai'
