"""Use the selected agent for inference, with independent media and embeddings."""

from contextlib import contextmanager
from contextvars import ContextVar
import json
from pathlib import Path
from threading import Event

from askai.core.agents.contracts import AgentError, AgentTask
from askai.core.agents.factory import create_backend, normalize_agent
from askai.core.model.ai_reply import AIReply


class AgentEngine:
    def __init__(self, name: str, model: str | None = None):
        self.name = normalize_agent(name)
        self.model = model
        self.backend = create_backend(self.name, debug=lambda: self.configs().is_debug)
        self._session = ContextVar("agent_review_session", default=None)
        self._embeddings = None

    def nickname(self):
        return self.name.title()

    def ai_name(self):
        return self.nickname()

    def ai_model_name(self):
        return self.model or "runtime default"

    def ai_token_limit(self):
        return self.backend.context_window(self.model)

    def configs(self):
        from askai.core.askai_configs import configs

        return configs

    def models(self):
        raise NotImplementedError(
            "Model catalogue is managed by the selected agent CLI. Use -m for an explicit model."
        )

    @contextmanager
    def use_session(self, session_id: str):
        token = self._session.set(session_id)
        try:
            yield
        finally:
            self._session.reset(token)

    def complete(
        self, messages: list[dict], temperature: float = 0.0, schema: dict | None = None
    ) -> str:
        instruction = (
            "Taius text-only inference task messages:\n"
            + json.dumps(messages, ensure_ascii=False)
        )

        def deny(method, params):
            raise AgentError(f"Text-only inference unexpectedly requested {method}")

        result = self.backend.run(
            AgentTask(
                instruction,
                Path.cwd(),
                session_id=self._session.get(),
                model=self.model,
                output_schema=schema,
                read_only=True,
                persist_history=(bool(self._session.get()) and self.configs().is_keep_context and
                                 self.backend.session_is_private(self._session.get()) is not True),
            ),
            lambda event: None,
            deny,
            Event(),
        )
        if result.status != "completed":
            raise AgentError("Agent inference was interrupted")
        return result.answer

    def ask(
        self, chat_context: list[dict], temperature: float = 0.8, top_p: float = 0.0
    ):
        return AIReply.info(self.complete(chat_context, temperature))

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._embeddings is None:
            from chromadb.utils.embedding_functions.onnx_mini_lm_l6_v2 import (
                ONNXMiniLM_L6_V2,
            )

            self._embeddings = ONNXMiniLM_L6_V2()
        return [vector.tolist() for vector in self._embeddings(texts)]

    def embedding_key(self):
        return "local:onnx:all-MiniLM-L6-v2"

    def vision(self):
        raise NotImplementedError(
            "Image attachments for agent backends are not integrated yet"
        )

    def calculate_tokens(self, text: str) -> int:
        import tiktoken

        return len(tiktoken.get_encoding("cl100k_base").encode(text))
