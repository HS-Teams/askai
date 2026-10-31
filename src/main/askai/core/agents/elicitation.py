"""MCP form decoding and validation, independent of terminal or TUI."""

import json
from jsonschema import validate

ELICITATION_METHOD = "mcpServer/elicitation/request"
INPUT_FORM_METHOD = "askai/input/request"
FORM_MODES = {"form", "openai/form", "openaiForm"}


def field_label(name, schema, translate=lambda text: text):
    label = translate(schema["title"]) if schema.get("title") else name
    if description := schema.get("description"):
        label += " — " + translate(description)
    choices = schema.get("enum") or schema.get("oneOf") or schema.get("anyOf")
    if choices:
        labels = [translate(choice.get("title", str(choice.get("const", ""))))
                  if isinstance(choice, dict) else str(choice) for choice in choices]
        label += "\n" + translate("Options:") + "  " + "    ".join(
            f"({index}) {title}" for index, title in enumerate(labels, 1)
        )
    if schema.get("type") in ("object", "array"):
        label += " (JSON)"
    return label


def decode_form(schema, values):
    result = {}
    for name, field in schema.get("properties", {}).items():
        value = values.get(name, "")
        if value == "" and name not in schema.get("required", []):
            continue
        choices = field.get("enum") or field.get("oneOf") or field.get("anyOf")
        if choices:
            constants = [choice.get("const") if isinstance(choice, dict) else choice for choice in choices]
            if value not in constants and value.isdecimal() and 1 <= int(value) <= len(constants):
                value = constants[int(value) - 1]
        kind = field.get("type", "string")
        if kind == "boolean":
            normalized = value.strip().casefold().rstrip(".!?")
            if normalized in {"sim", "s", "yes", "true", "1"}:
                value = True
            elif normalized in {"não", "nao", "n", "no", "false", "0"}:
                value = False
            else:
                raise ValueError(f"{name}: enter yes or no")
        elif kind != "string":
            value = json.loads(value)
        result[name] = value
    validate(result, schema)
    return result


def validate_reply(params, response):
    if response.get("action") not in {"accept", "decline", "cancel"}:
        raise ValueError("Invalid MCP elicitation action")
    if response["action"] == "accept" and params.get("mode", "form") in FORM_MODES:
        validate(response.get("content"), params["requestedSchema"])
