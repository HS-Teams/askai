"""Fan out application messages to screen, session, journal and diagnostic log."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from threading import RLock
from uuid import uuid4


SESSION_MESSAGES = 100


class CommunicationBus:
    def __init__(self, *, session_id=None, journal=None, recording=lambda: False, logger=None):
        self.session_id = session_id or uuid4().hex
        self._journal = Path(journal) if journal else None
        self._recording = recording
        self._logger = logger or logging.getLogger(__name__)
        self._messages = deque(maxlen=SESSION_MESSAGES)
        self._lock = RLock()

    def configure(self, session_id, journal, recording):
        with self._lock:
            self.session_id = session_id
            self._journal = Path(journal)
            self._recording = recording
            self._messages.clear()

    def publish(self, kind, payload, *, screen=None, remember=True, record=True):
        event = {
            'id': uuid4().hex, 'session_id': self.session_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'kind': kind, 'payload': deepcopy(payload),
            'delivery_errors': [],
        }
        errors = []
        with self._lock:
            try:
                recording = record and self._recording()
            except Exception as error:
                recording = False
                errors.append({'destination': 'recording_policy', 'error_type': type(error).__name__})
            if recording:
                for destination, sink in (('file', self._write_file), ('log', self._write_log)):
                    try:
                        sink(event)
                    except Exception as error:
                        errors.append({'destination': destination, 'error_type': type(error).__name__})
            if remember:
                self._messages.append(event)
        if screen is not None:
            try:
                screen()
            except Exception as error:
                errors.append({'destination': 'screen', 'error_type': type(error).__name__})
        with self._lock:
            event['delivery_errors'] = errors
        if errors:
            try:
                self._logger.error('Communication delivery failed: %s', errors)
            except Exception:
                # Delivery errors remain available in the session if logging itself fails.
                pass
        return deepcopy(event)

    def recent(self, kind=None, limit=10):
        with self._lock:
            messages = [event for event in self._messages if kind is None or event['kind'] == kind]
            return deepcopy(messages[-limit:]) if limit > 0 else []

    def clear(self):
        with self._lock:
            self._messages.clear()

    def _write_file(self, event):
        if self._journal is not None:
            self._journal.parent.mkdir(parents=True, exist_ok=True)
            with self._journal.open('a', encoding='utf-8') as journal:
                journal.write(json.dumps(event, ensure_ascii=False, default=str) + '\n')

    def _write_log(self, event):
        failed = event['payload'].get('status') == 'failed' or event['payload'].get('is_success') is False
        self._logger.log(logging.WARNING if failed else logging.INFO,
                         'AskAI communication: %s', json.dumps(event, ensure_ascii=False, default=str))


communication = CommunicationBus()


def configure_communication(session_id, recording):
    from askai.core.support.app_paths import askai_data_dir

    run_id = f'{session_id}-{uuid4().hex}'
    communication.configure(run_id, askai_data_dir() / 'sessions' / 'communication' / f'{run_id}.jsonl', recording)


class ReplyChannel:
    """Keep the existing CLI/TUI event delivery behind the communication bus."""
    def __init__(self, channel):
        self._channel = channel

    def emit(self, **kwargs):
        reply = kwargs.get('reply')
        payload = {'message': str(getattr(reply, 'message', kwargs.get('message', ''))),
                   'is_success': getattr(reply, 'is_success', True),
                   'is_final': getattr(reply, 'is_final', False)}
        return communication.publish('reply', payload, screen=lambda: self._channel.emit(**kwargs))

    def subscribe(self, *args, **kwargs):
        return self._channel.subscribe(*args, **kwargs)
