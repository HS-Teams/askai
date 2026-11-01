"""Transient terminal progress for orchestration and agent activity."""

from rich.status import Status


class AgentProgress:
    _STAGES = {
        "retrieval": "Consultando contexto e fontes…",
        "execution": "Processando solicitação…",
        "validation": "Validando resposta…",
        "refinement": "Refinando resposta…",
    }
    _ACTIVITIES = {
        "commandExecution": "Executando comando…",
        "fileChange": "Alterando arquivos…",
        "mcpToolCall": "Consultando ferramenta…",
        "webSearch": "Pesquisando na web…",
        "reasoning": "Analisando solicitação…",
        "agentMessage": "Preparando resposta…",
    }

    def __init__(self, console, interact):
        self._status = Status("", console=console, spinner="dots")
        self._interact = interact
        self._active = False

    def emit(self, event):
        if event.kind in {"camera_started", "screenshot_started"}:
            self._status.stop()
            return
        if event.kind in {"camera_finished", "screenshot_finished"}:
            if self._active:
                self._status.start()
            return
        if event.kind == "finished":
            self._status.stop()
            self._active = False
            return
        label = None
        if event.kind == "stage":
            label = self._STAGES.get(event.data.get("stage"))
            if event.data.get("stage") == "compaction":
                from askai.core.askai_messages import msg
                label = msg.translate("Compactando histórico…")
        elif event.kind == "progress":
            label = self._ACTIVITIES.get(event.data.get("type"), "Processando solicitação…")
        elif event.kind == "tool_progress":
            from askai.core.askai_messages import msg
            label = msg.t(event.data.get("message", ""))
        elif event.kind == "tool_completed":
            label = "Analisando resultado da ferramenta…"
        if label:
            self._status.update(label)
            if not self._active:
                self._status.start()
                self._active = True

    def present(self, render):
        """Print a permanent assistant message outside the live spinner."""
        self._status.stop()
        try:
            render()
        finally:
            if self._active:
                self._status.start()

    def interact(self, method, params):
        """Leave the terminal free while a question or approval awaits input."""
        self._status.stop()
        try:
            return self._interact(method, params)
        finally:
            if self._active:
                self._status.start()
