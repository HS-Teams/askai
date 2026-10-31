"""Access the configured native inference provider from application services."""


def complete(
    messages: str | list[dict], temperature: float = 0.0, schema: dict | None = None
) -> str:
    from askai.core.support.shared_instances import shared

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]
    return shared.engine.complete(messages, temperature, schema)
