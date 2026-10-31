"""MCP form decoding and validation, independent of terminal or TUI."""

import json
from jsonschema import validate

ELICITATION_METHOD = "mcpServer/elicitation/request"
FORM_MODES = {"form", "openai/form", "openaiForm"}


def field_label(name, schema, translate=lambda text: text):
    label = translate(schema["title"]) if schema.get("title") else name
    if description := schema.get("description"):
        label += " — " + translate(description)
    choices = schema.get("enum") or schema.get("oneOf") or schema.get("anyOf")
    if choices:
        label += (
            "\n" + translate("Options:") + " " + json.dumps(choices, ensure_ascii=False)
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
