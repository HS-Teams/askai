"""Document-grounded conversation, retaining AskAI's RAG functionality."""
from askai.core.component.rag_provider import RAG_EXT_DIR
from askai.core.component.summarizer import Summarizer
from askai.exception.exceptions import TerminatingQuery


class Rag:
    def __init__(self):
        self._retrieval = Summarizer()

    def prepare(self):
        from askai.core.askai_configs import configs
        if configs.is_rag and any(RAG_EXT_DIR.glob("**/*.md")):
            if not self._retrieval.exists(RAG_EXT_DIR, "**/*.md"):
                self._retrieval.generate(RAG_EXT_DIR, "**/*.md")

    def retrieve(self, question: str) -> str:
        if not self._retrieval.exists(RAG_EXT_DIR, "**/*.md"):
            self._retrieval.generate(RAG_EXT_DIR, "**/*.md")
        return self._retrieval.retrieve(question)

    def process(self, question: str, **kwargs) -> str:
        if not question:
            raise TerminatingQuery("The user wants to exit!")
        if question.casefold() in {"exit", "leave", "quit", "q"}:
            from askai.core.askai_events import events
            events.mode_changed.emit(mode="DEFAULT")
            return None
        self.retrieve(question)
        return self._retrieval.query(question)[0].answer

    def generate(self, rag_dir=RAG_EXT_DIR, file_glob="**/*.md"):
        return self._retrieval.generate(rag_dir, file_glob)


rag = Rag()
