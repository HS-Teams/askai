"""Coordinate AskAI capabilities without reproducing an agent's tool loop."""

from contextlib import nullcontext
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from askai.core.support.performance import request_timing, timed
from datetime import date
from pathlib import Path
from threading import Event, Lock
from askai.core.agents.contracts import AgentBackend, AgentTask, AgentError, AgentEvent, AgentSessionNotFound


class Orchestrator:
    def __init__(
        self,
        backend: AgentBackend,
        memory,
        retrieve,
        validate,
        refine,
        model: str | None = None,
        durable=None,
        agent_name: str = "codex",
        review_scope=None,
        today=date.today,
        resume_history=lambda: True,
        prepare=None,
    ):
        self._backend, self._memory = backend, memory
        self._review_scope = review_scope or (lambda session: nullcontext())
        self._today = today
        self._resume_history = resume_history
        self._prepare = prepare
        self._model = model
        self._durable, self._agent_name = durable, agent_name
        self._retrieve, self._validate, self._refine = retrieve, validate, refine
        self.cancelled = Event()
        self._active = Lock()
        self._sessions: dict[tuple[str, str], str] = {}
        self._last_session_key = None
        self._record_history = None

    def reset_session(self, cwd: Path, emit=lambda event: None) -> None:
        if not self._active.acquire(blocking=False):
            raise AgentError(
                "Wait for the current task to finish before resetting its session"
            )
        try:
            day = self._today().isoformat()
            key = str(cwd.resolve())
            from askai.core.orchestration.session_reset import reset_saved_session

            reset_saved_session(
                self._backend, self._durable if self._resume_history() else None,
                self._agent_name, key, day, self._sessions.get((key, day)),
                emit=emit, model=self._model,
            )
            self._sessions.pop((key, day), None)
            self._last_session_key = None
        finally:
            self._active.release()

    def set_model(self, model):
        if not self._active.acquire(blocking=False):
            raise AgentError('Wait for the current task to finish before changing the model')
        try:
            self._model = model
        finally:
            self._active.release()

    def compact_session(self, cwd: Path, emit, *, wait=False) -> bool:
        acquired = self._active.acquire(timeout=30) if wait else self._active.acquire(blocking=False)
        if not acquired:
            raise AgentError("Wait for the current task to finish before compacting its session")
        try:
            if wait and self.cancelled.is_set():
                return False
            key, day = self._last_session_key or (str(cwd.resolve()), self._today().isoformat())
            if self._durable is None or not self._resume_history():
                return False
            from askai.core.orchestration.session_compaction import compact_saved_session

            return compact_saved_session(
                self._backend, self._durable, self._agent_name, key, day, emit,
                session=self._sessions.get((key, day)), model=self._model,
            )
        finally:
            self._active.release()
            emit(AgentEvent("finished", ""))

    @request_timing()
    def process(self, question: str, cwd: Path, context: str, emit, interact) -> str:
        if not self._active.acquire(blocking=False):
            raise AgentError(
                "Taius is already processing an objective; cancel it or wait for completion"
            )
        request = None
        day = self._today().isoformat()
        key = str(cwd.resolve())
        session_key = (key, day)
        self._last_session_key = session_key
        original_emit, original_interact = emit, interact
        recording = bool(self._resume_history())
        if self._record_history is not None and self._record_history != recording:
            self._sessions.clear()
        self._record_history = recording
        try:
            if self._durable and recording:
                if session_key not in self._sessions and self._resume_history():
                    session = self._durable.session(self._agent_name, key, day)
                    if session:
                        self._sessions[session_key] = session
                    elif previous := self._durable.previous_session(self._agent_name, key, day):
                        from askai.core.orchestration.session_compaction import compact_saved_session
                        previous_day, previous_session = previous
                        try:
                            compact_saved_session(
                                self._backend, self._durable, self._agent_name, key,
                                previous_day, emit, session=previous_session, model=self._model,
                            )
                        except AgentSessionNotFound as error:
                            from askai.core.orchestration.session_reset import retire_missing_session
                            retire_missing_session(self._durable, self._agent_name, key,
                                                   previous_day, previous_session, error)
                            self._sessions.pop((key, previous_day), None)
                request = self._durable.begin(self._agent_name, key, question, day=day)

                def emit(event):
                    if event.kind in {
                        "started",
                        "tool_completed",
                        "completed",
                        "cancelled",
                        "result",
                    }:
                        self._durable.record(
                            self._agent_name,
                            key,
                            request,
                            event.kind,
                            {"turn": event.turn_id, "data": event.data},
                            event.session_id,
                            session_date=day,
                        )
                    original_emit(event)

                def interact(method, params):
                    decision = original_interact(method, params)
                    # Never persist secret answers requested by an agent.
                    private = method == "mcpServer/elicitation/request" or any(
                        q.get("isSecret") for q in params.get("questions", [])
                    )
                    self._durable.record(
                        self._agent_name,
                        key,
                        request,
                        "decision",
                        {
                            "method": method,
                            "request": "[private]" if private else params,
                            "response": "[private]" if private else decision,
                        },
                    )
                    return decision

            answer = self._process(question, cwd, context, emit, interact, day)
            if self._durable and request:
                self._durable.record(
                    self._agent_name,
                    key,
                    request,
                    "final_answer",
                    {"text": answer},
                    self._sessions.get(session_key),
                    session_date=day,
                )
            return answer
        except BaseException as error:
            if self._durable and request:
                self._durable.record(
                    self._agent_name, key, request, "failed", {"error": str(error)}
                )
            raise
        finally:
            self._active.release()
            emit(AgentEvent("finished", ""))

    def _process(
        self, question: str, cwd: Path, context: str, emit, interact, day: str
    ) -> str:
        self.cancelled.clear()
        self._memory.add("human", question, recordable=bool(self._record_history))
        self._memory.pending["objective"] = question
        emit(AgentEvent("stage", "", data={"stage": "retrieval"}))
        with timed("retrieval_and_connection"):
            if self._prepare is None:
                retrieved = self._retrieve(question)
            else:
                with ThreadPoolExecutor(max_workers=1, thread_name_prefix="askai-connect") as pool:
                    ready = pool.submit(copy_context().run, self._prepare)
                    retrieved = self._retrieve(question)
                    ready.result()
        if retrieved:
            context += "\n\nRetrieved sources:\n" + retrieved
        if self.cancelled.is_set():
            raise AgentError("Request cancelled before execution")
        key = (str(cwd.resolve()), day)
        from askai.core.speech.dictation_memory import context as dictation_context

        latest_dictation = dictation_context(
            self._memory, self._durable if self._record_history else None,
            self._agent_name, cwd,
        )
        if latest_dictation:
            context += "\n\n" + latest_dictation
        task = AgentTask(
            question,
            cwd,
            context,
            self._sessions.get(key),
            model=self._model,
            session_name=day,
            persist_history=self._record_history,
        )
        emit(AgentEvent("stage", "", data={"stage": "execution"}))
        with timed("execution"):
            result = self._backend.run(task, emit, interact, self.cancelled)
        self._sessions[key] = result.session_id
        emit(
            AgentEvent(
                "result",
                result.session_id,
                result.turn_id,
                {
                    "answer": result.answer,
                    "status": result.status,
                    "evidence": result.evidence,
                },
            )
        )
        if result.status != "completed":
            raise AgentError("Delegated task cancelled; completed actions may remain")
        answer, evidence = result.answer, result.evidence
        if self.cancelled.is_set():
            raise AgentError(
                "Request cancelled after generation; actions were not rolled back"
            )
        with self._review_scope(result.session_id):
            emit(AgentEvent("stage", result.session_id, data={"stage": "validation"}))
            with timed("validation"):
                assessment = self._validate(question, answer, evidence)
            if self.cancelled.is_set():
                raise AgentError("Request cancelled before refinement")
            emit(AgentEvent("stage", result.session_id, data={"stage": "refinement"}))
            with timed("refinement"):
                answer = self._refine(question, answer, assessment)
        if not answer or not answer.strip():
            raise AgentError("Taius produced no final answer")
        self._memory.add("assistant", answer, recordable=bool(self._record_history))
        self._memory.pending.pop("objective", None)
        return answer
