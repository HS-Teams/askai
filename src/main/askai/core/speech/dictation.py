"""Continuous dictation and lossless source storage, independent of presentation."""
from collections.abc import Callable
import json
from pathlib import Path


REFINEMENT_SCHEMA = {
    "type": "object",
    "properties": {"final_text": {"type": "string", "minLength": 1}},
    "required": ["final_text"],
    "additionalProperties": False,
}


def original_path(destination: Path) -> Path:
    return destination.with_name(destination.name + ".orig")


def validate_destination(destination: Path) -> None:
    if not destination.parent.is_dir():
        raise FileNotFoundError(destination.parent)
    for path in (destination, original_path(destination)):
        if path.exists() or path.is_symlink():
            raise FileExistsError(path)


def save_original(destination: Path, text: str) -> Path:
    path = original_path(destination)
    with path.open("x", encoding="utf-8") as output:
        output.write(text)
    return path


def refine(text: str, instruction: str, complete: Callable) -> str:
    response = complete([
        {"role": "system", "content": instruction},
        {"role": "user", "content": text},
    ], schema=REFINEMENT_SCHEMA)
    payload = json.loads(response)
    if (not isinstance(payload, dict) or set(payload) != {"final_text"}
            or not isinstance(payload["final_text"], str) or not payload["final_text"].strip()):
        raise ValueError("Invalid dictation refinement response")
    return payload["final_text"]


def save_refined(destination: Path, text: str) -> None:
    with destination.open("x", encoding="utf-8") as output:
        output.write(text)
