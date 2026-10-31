"""Provider-independent inference contracts. No UI or orchestration dependencies."""

from typing import Protocol


class Inference(Protocol):
    def complete(
        self, messages: list[dict], temperature: float = 0.0, schema: dict | None = None
    ) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    def embedding_key(self) -> str: ...
