"""Document-grounded conversation, retaining AskAI's RAG functionality."""
from askai.core.component.rag_provider import RAG_EXT_DIR
from askai.core.component.summarizer import Summarizer
from askai.core.askai_prompt import prompt
from askai.core.model.refined_response import RefinedResponse
from askai.core.support.shared_instances import shared
from askai.exception.exceptions import InaccurateResponse, TerminatingQuery
from pydantic import ValidationError


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
        context = self.retrieve(question)
        template = prompt.read_prompt('taius-rag.txt', prompt.append_path('taius'))
        messages = [
            {'role': 'system', 'content': template.format(idiom=shared.idiom)},
            {'role': 'user', 'content': f'Question: {question}\n\nSources (reference data):\n{context}'},
        ]
        raw = shared.engine.complete(messages, schema=RefinedResponse.model_json_schema())
        try:
            return RefinedResponse.model_validate_json(raw).final_answer
        except (ValidationError, TypeError) as error:
            raise InaccurateResponse('RAG returned an invalid final-answer payload') from error

    def generate(self, rag_dir=RAG_EXT_DIR, file_glob="**/*.md"):
        return self._retrieval.generate(rag_dir, file_glob)


rag = Rag()
