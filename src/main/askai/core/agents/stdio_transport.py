"""JSONL transport with bounded waits and deterministic subprocess cleanup."""

import json
import queue
import subprocess
import threading
from collections import deque
from time import monotonic

from askai.core.agents.contracts import AgentError


class StdioTransport:
    def __init__(self, command: list[str], timeout: float = 120):
        self._command = command
        self._timeout = timeout
        self._incoming = queue.Queue()
        self._pending = deque()
        self._counter = 0
        self._process = None
        self._threads = []

    def __enter__(self):
        try:
            self._process = subprocess.Popen(
                self._command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
            )
        except OSError as error:
            raise AgentError(f"Cannot start {self._command[0]}: {error}") from error
        self._threads = [
            threading.Thread(target=self._read, daemon=True),
            threading.Thread(target=self._drain_errors, daemon=True),
        ]
        for thread in self._threads:
            thread.start()
        return self

    def __exit__(self, *_):
        process = self._process
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()
            for thread in self._threads:
                thread.join(timeout=1)

    def send(self, message: dict) -> None:
        try:
            self._process.stdin.write(json.dumps(message) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, OSError) as error:
            raise AgentError(
                "Codex transport closed while sending a message"
            ) from error

    def request(self, method: str, params: dict) -> dict:
        self._counter += 1
        request_id = self._counter
        self.send({"id": request_id, "method": method, "params": params})
        deadline = monotonic() + self._timeout
        while monotonic() < deadline:
            message = self._receive(min(0.2, max(0.01, deadline - monotonic())))
            if message is None:
                continue
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    from askai.core.agents.contracts import AgentSessionNotFound

                    error = message['error']
                    session = params.get('threadId')
                    if (method in {'thread/resume', 'thread/archive', 'thread/compact/start'}
                            and session and isinstance(error, dict)
                            and error.get('code') == -32600
                            and error.get('message') == f'no rollout found for thread id {session}'):
                        raise AgentSessionNotFound(f'Codex {method}: {error}')
                    raise AgentError(f"Codex {method}: {error}")
                if not isinstance(message.get("result"), dict):
                    raise AgentError(f"Invalid Codex response to {method}")
                return message["result"]
            self._pending.append(message)
        raise AgentError(
            f"Codex request timed out: {method}; execution status may be unknown"
        )

    def receive(self, timeout: float = 0.2) -> dict | None:
        return self._pending.popleft() if self._pending else self._receive(timeout)

    def _receive(self, timeout: float) -> dict | None:
        try:
            value = self._incoming.get(timeout=timeout)
        except queue.Empty:
            return None
        if isinstance(value, Exception):
            raise value
        return value

    def _read(self):
        try:
            for line in self._process.stdout:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("Expected a JSON object")
                self._incoming.put(message)
        except (ValueError, OSError) as error:
            self._incoming.put(AgentError(f"Invalid Codex transport: {error}"))
        finally:
            self._incoming.put(AgentError("Codex process closed before completion"))

    def _drain_errors(self):
        # Drain independently to prevent pipe deadlocks; never log tokens or prompts.
        for _ in self._process.stderr:
            pass
