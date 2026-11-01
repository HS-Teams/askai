"""Application wiring for the view-independent orchestration service."""

from pathlib import Path
from askai.core.support.performance import timed
from askai.core.component.answer_refiner import refine_response
from askai.core.orchestration.orchestrator import Orchestrator


class TaiusProcessor:
    cacheable = False

    def __init__(self):
        self._orchestrator = None
        self._exit_compaction_done = False
        self.emit = lambda event: None
        self.interact = self._missing_interaction

    @staticmethod
    def _missing_interaction(method, params):
        from askai.core.agents.contracts import AgentError

        raise AgentError(f"No view is connected to handle {method}")

    def cancel(self):
        if self._orchestrator:
            self._orchestrator.cancelled.set()

    def set_model(self, model):
        if self._orchestrator is not None:
            self._orchestrator.set_model(model)

    def reset_session(self):
        from askai.core.askai_configs import configs
        if not configs.is_keep_context and self._orchestrator is None:
            return
        if self._orchestrator:
            self._orchestrator.reset_session(Path.cwd())
        else:
            from datetime import date
            from askai.core.askai_configs import configs
            from askai.core.askai_settings import ASKAI_DIR
            from askai.core.support.persistent_memory import PersistentMemory

            from askai.core.support.shared_instances import shared
            from askai.core.orchestration.session_reset import reset_saved_session

            reset_saved_session(
                shared.engine.backend,
                PersistentMemory(Path(ASKAI_DIR) / "memory" / "history.sqlite3"),
                configs.agent, str(Path.cwd().resolve()), date.today().isoformat()
            )

    def compact_session(self, *, wait=False):
        from askai.core.askai_configs import configs
        if not configs.is_keep_context:
            return False
        if self._orchestrator:
            return self._orchestrator.compact_session(Path.cwd(), self.emit, wait=wait)
        from datetime import date
        from askai.core.askai_configs import configs
        from askai.core.askai_settings import ASKAI_DIR
        from askai.core.support.persistent_memory import PersistentMemory
        from askai.core.support.shared_instances import shared
        from askai.core.orchestration.session_compaction import compact_saved_session
        from askai.core.agents.contracts import AgentEvent

        try:
            return compact_saved_session(
                shared.engine.backend,
                PersistentMemory(Path(ASKAI_DIR) / "memory" / "history.sqlite3"),
                configs.agent, str(Path.cwd().resolve()), date.today().isoformat(), self.emit,
                model=shared.engine.model,
            )
        finally:
            self.emit(AgentEvent("finished", ""))

    def compact_on_exit(self):
        from askai.core.askai_configs import configs
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply
        from askai.core.askai_messages import msg
        import logging

        if self._exit_compaction_done or not configs.is_keep_context or not configs.compact_on_exit or self._orchestrator is None:
            return
        self._exit_compaction_done = True
        if self._orchestrator.cancelled.is_set():
            return
        try:
            self.compact_session(wait=True)
        except Exception as error:
            logging.warning("Session compaction on exit failed: %s", error)
            events.reply.emit(reply=AIReply.error(msg.t("Session compaction could not be confirmed. Your history was preserved.")))

    def process(self, question: str, **kwargs):
        from askai.core.askai_prompt import prompt
        from askai.core.askai_configs import configs
        from askai.core.component.cache_service import cache
        from askai.core.processors.rag import rag
        from askai.core.component.answer_validator import validate_response
        from askai.core.support.shared_instances import shared
        from askai.exception.exceptions import InaccurateResponse, TerminatingQuery

        if not question or question.casefold() in {"exit", "leave", "quit", "q"}:
            raise TerminatingQuery("The user wants to exit!")

        def retrieve(query):
            from askai.core.component.rag_provider import RAG_EXT_DIR

            if not configs.is_rag or not any(RAG_EXT_DIR.glob("**/*.md")):
                return ""
            return rag.retrieve(query)

        def validate(query, answer, evidence):
            report = validate_response(
                shared.engine,
                prompt.read_prompt(
                    "taius-session-validator.txt", prompt.append_path("taius")
                ),
            )
            if not report.is_pass(configs.pass_threshold):
                raise InaccurateResponse(report.details)
            return report

        def refine(query, answer, report):
            from askai.core.component.search_presentation import search_refinement_instructions

            template = prompt.read_prompt(
                "taius-session-refiner.txt", prompt.append_path("taius")
            )
            return refine_response(
                shared.engine,
                template,
                assistive_instructions=(
                    prompt.read_prompt("taius-tts.txt", prompt.append_path("taius"))
                    if configs.is_assistive or configs.is_speak
                    else ""
                ),
                search_instructions=search_refinement_instructions(configs.stt_language.idiom),
                locale=configs.stt_language.idiom,
                user=prompt.user.title(),
            )

        if self._orchestrator is None:
            from askai.core.askai_settings import ASKAI_DIR
            from askai.core.support.persistent_memory import PersistentMemory

            self._orchestrator = Orchestrator(
                shared.engine.backend,
                shared.memory,
                retrieve,
                validate,
                refine,
                model=shared.engine.model,
                durable=PersistentMemory(
                    Path(ASKAI_DIR) / "memory" / "history.sqlite3"
                ),
                agent_name=configs.agent,
                review_scope=shared.engine.use_session,
                prepare=shared.engine.backend.prepare,
                resume_history=lambda: configs.is_keep_context,
            )
        context = kwargs.get("context") or ""
        try:
            return self._orchestrator.process(
                question, Path.cwd(), context, self.emit, self.interact
            )
        finally:
            with timed("memory.snapshot"):
                cache.save_memory(shared.memory.messages)
                shared.context.save()


taius = TaiusProcessor()
