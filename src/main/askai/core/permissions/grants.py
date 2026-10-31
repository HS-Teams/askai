"""Exact, live settings grants. Unknown permissions never authorize an action."""
from enum import Enum
import sqlite3
import os
from pathlib import Path
from askai.core.support.app_paths import askai_data_dir
from askai.core.agents.elicitation import ELICITATION_METHOD, validate_reply

PREFIX = 'askai.grants.'
GRANTS = {
    'camera.capture.local': 'Capture a local camera photo',
    'camera.preview.local': 'Open the camera preview',
    'screen.capture.local': 'Capture the local screen',
    'vision.share.agent': 'Share a captured image with the agent',
    'images.read.local': 'Read photos and open numbered previews for enrollment',
    'identities.read.local': 'Read local identities and their samples',
    'identities.create.local': 'Create named face samples',
    'identities.merge.local': 'Merge face samples into an identity',
    'identities.replace.local': 'Replace all samples of an identity',
    'media.play.local': 'Play or resume local media',
    'media.pause.local': 'Pause local media',
    'media.stop.local': 'Stop local media',
    'paths.open.local': 'Open local files or folders',
    'applications.open.local': 'Launch a local application',
}


class GrantValue(str, Enum):
    ASK = 'ask'
    ALLOW = 'allow'
    DENY = 'deny'


class GrantDenied(PermissionError):
    pass


def grant_key(name: str) -> str:
    short = name.removeprefix(PREFIX)
    if short not in GRANTS:
        raise ValueError(f'Unknown grant: {name}')
    return PREFIX + short


def validate_setting(name: str, value) -> str:
    grant_key(name)
    if not isinstance(value, str):
        raise ValueError('Grant value must be ask, allow or deny')
    try:
        return GrantValue(value.strip().lower()).value
    except ValueError:
        raise ValueError('Grant value must be ask, allow or deny') from None


def read_grant(key: str) -> str:
    """Read the shared SetMan database without creating services or caching policy."""
    path = askai_data_dir() / 'askai.db'
    if not path.exists():
        return GrantValue.ASK.value
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True)
    try:
        row = db.execute('SELECT value FROM SETTINGS WHERE name=?', (key,)).fetchone()
        return row[0] if row else GrantValue.ASK.value
    finally:
        db.close()


class GrantPolicy:
    def __init__(self, read=read_grant):
        self._read = read

    @staticmethod
    def check_scope():
        if scope := os.environ.get("ASKAI_ACTION_SCOPE_FILE"):
            try:
                allowed = Path(scope).read_text() == "allow"
            except OSError:
                allowed = False
            if not allowed:
                raise GrantDenied("AskAI actions are disabled outside an execution turn")

    def pending(self, names) -> list[str]:
        """Check the entire operation before asking or executing any part of it."""
        self.check_scope()
        pending = []
        for name in dict.fromkeys(names):
            key = grant_key(name)
            try:
                value = GrantValue(self._read(key))
            except (ValueError, TypeError):
                raise GrantDenied(f'Invalid grant value; action blocked: {key}') from None
            if value == GrantValue.DENY:
                raise GrantDenied(f'Action blocked by setting: {key}')
            if value == GrantValue.ASK:
                pending.append(key)
        return pending

    def authorize(self, names, message, interact) -> bool:
        if not self.pending(names):
            return True
        request = self.request(message)
        response = interact(ELICITATION_METHOD, request)
        validate_reply(request, response)
        self.pending(names)
        return response['action'] == 'accept'

    async def authorize_async(self, names, message, confirm) -> bool:
        if not self.pending(names):
            return True
        accepted = await confirm(message)
        self.pending(names)
        return accepted is True

    @staticmethod
    def request(message):
        return {'serverName': 'AskAI', 'mode': 'form', 'message': message,
                'requestedSchema': {'type': 'object', 'properties': {}}}


grants = GrantPolicy()
