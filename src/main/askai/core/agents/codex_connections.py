"""Reuse one app-server, granting desktop actions only during execution leases."""
import atexit
from contextlib import contextmanager
from threading import RLock
from tempfile import TemporaryDirectory
from pathlib import Path

from askai.core.agents.contracts import AgentError
from askai.core.agents.desktop_tools import app_server_command
from askai.core.support.performance import timed


class CodexConnections:
    def __init__(self, executable, factory):
        self._executable, self._factory = executable, factory
        self._connection = None
        self._lock = RLock()
        self._registered = False
        self._scope_directory = None
        self._lease_scopes = []

    def prepare(self):
        with self._lock, timed('codex.connection.reused' if self._connection else 'codex.connection.cold'):
            if self._connection is None:
                if self._lease_scopes:
                    raise AgentError('Codex connection was closed during an active lease')
                self._scope_directory = TemporaryDirectory(prefix="askai-action-scope-")
                try:
                    self._set_action_scope(False)
                    manager = self._factory(app_server_command(self._executable, False, str(self._scope_file)))
                    self._connection = manager, None
                    transport = manager.__enter__()
                    transport.request('initialize', {'clientInfo': {'name': 'askai', 'version': '1.0.0'}, 'capabilities': {'experimentalApi': True}})
                    transport.send({'method': 'initialized', 'params': {}})
                    account = transport.request('account/read', {}).get('account') or {}
                    if account.get('type') != 'chatgpt':
                        raise AgentError('Codex requires a ChatGPT login. Run `codex login` first (API keys are not used).')
                except BaseException:
                    self._discard()
                    raise
                self._connection = manager, transport
                if not self._registered:
                    atexit.register(self.close)
                    self._registered = True
            return self._connection[1]

    @contextmanager
    def lease(self, read_only, *, actions_allowed=None):
        with self._lock:
            allowed = not read_only and (True if actions_allowed is None else actions_allowed)
            if self._lease_scopes and allowed and not self._lease_scopes[-1]:
                raise AgentError('Cannot enable actions inside a read-only Codex lease')
            transport = self.prepare()
            self._lease_scopes.append(allowed)
            try:
                self._set_action_scope(allowed)
                yield transport
            except BaseException:
                self._discard()
                raise
            finally:
                self._lease_scopes.pop()
                if self._connection is not None:
                    try:
                        self._set_action_scope(self._lease_scopes[-1] if self._lease_scopes else False)
                    except BaseException:
                        self._discard()
                        raise

    def revoke_actions(self):
        """Cancellation cannot restore an enclosing execution's permissions."""
        with self._lock:
            self._lease_scopes[:] = [False] * len(self._lease_scopes)
            if self._connection is not None:
                try:
                    self._set_action_scope(False)
                except BaseException:
                    self._discard()
                    raise

    @property
    def _scope_file(self):
        return Path(self._scope_directory.name) / "execution"

    def _set_action_scope(self, allowed):
        temporary = self._scope_file.with_suffix(".tmp")
        temporary.write_text("allow" if allowed else "deny")
        temporary.replace(self._scope_file)

    def _discard(self):
        connection, self._connection = self._connection, None
        directory, self._scope_directory = self._scope_directory, None
        try:
            # Remove the grant before teardown, including if process shutdown fails.
            if directory is not None:
                directory.cleanup()
        finally:
            if connection:
                connection[0].__exit__(None, None, None)

    def close(self):
        with self._lock:
            try:
                self._discard()
            finally:
                if self._registered:
                    atexit.unregister(self.close)
                    self._registered = False
