"""Reuse app-server within a permission scope; release its writer on scope changes."""
import atexit
from contextlib import contextmanager
from threading import RLock
from tempfile import TemporaryDirectory
from pathlib import Path

from askai.core.agents.contracts import AgentError
from askai.core.agents.desktop_tools import app_server_command


class CodexConnections:
    def __init__(self, executable, factory):
        self._executable, self._factory = executable, factory
        self._connections = {}
        self._lock = RLock()
        self._registered = False
        self._scope_directory = None

    def prepare(self, read_only=False):
        with self._lock:
            if read_only not in self._connections:
                for scope in list(self._connections):
                    self._discard(scope)
                if self._scope_directory is None:
                    self._scope_directory = TemporaryDirectory(prefix="askai-action-scope-")
                self._set_action_scope(False)
                manager = self._factory(app_server_command(self._executable, read_only, str(self._scope_file)))
                transport = manager.__enter__()
                try:
                    transport.request('initialize', {'clientInfo': {'name': 'askai', 'version': '1.0.0'}, 'capabilities': {'experimentalApi': True}})
                    transport.send({'method': 'initialized', 'params': {}})
                    account = transport.request('account/read', {}).get('account') or {}
                    if account.get('type') != 'chatgpt':
                        raise AgentError('Codex requires a ChatGPT login. Run `codex login` first (API keys are not used).')
                except BaseException:
                    manager.__exit__(None, None, None)
                    self._scope_directory.cleanup()
                    self._scope_directory = None
                    raise
                self._connections[read_only] = manager, transport
                if not self._registered:
                    atexit.register(self.close)
                    self._registered = True
            return self._connections[read_only][1]

    @contextmanager
    def lease(self, read_only, *, actions_allowed=None):
        with self._lock:
            transport = self.prepare(read_only)
            self._set_action_scope(not read_only and (True if actions_allowed is None else actions_allowed))
            try:
                yield transport
            except BaseException:
                self._discard(read_only)
                raise
            finally:
                self._set_action_scope(False)

    @property
    def _scope_file(self):
        return Path(self._scope_directory.name) / "execution"

    def _set_action_scope(self, allowed):
        temporary = self._scope_file.with_suffix(".tmp")
        temporary.write_text("allow" if allowed else "deny")
        temporary.replace(self._scope_file)

    def _discard(self, read_only):
        connection = self._connections.pop(read_only, None)
        if connection:
            connection[0].__exit__(None, None, None)

    def close(self):
        with self._lock:
            for scope in list(self._connections):
                self._discard(scope)
            if self._registered:
                atexit.unregister(self.close)
                self._registered = False
            if self._scope_directory is not None:
                self._scope_directory.cleanup()
                self._scope_directory = None
