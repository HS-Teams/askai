"""Retire the runtime session before forgetting its local resume pointer."""
from uuid import uuid4
from askai.core.agents.contracts import AgentSessionNotFound


def reset_saved_session(backend, durable, agent, cwd, day, session=None, *, emit=lambda event: None, model=None):
    session = session or (durable.session(agent, cwd, day) if durable else None)
    if session:
        try:
            if durable:
                from askai.core.orchestration.session_compaction import compact_saved_session
                compact_saved_session(backend, durable, agent, cwd, day, emit,
                                      session=session, model=model)
            backend.archive(session)
        except AgentSessionNotFound as error:
            if durable:
                retire_missing_session(durable, agent, cwd, day, session, error)
            return
    if durable:
        durable.reset_session(agent, cwd, day)


def retire_missing_session(durable, agent, cwd, day, session, error):
    """Forget an unusable resume pointer while retaining the diagnostic history."""
    durable.record(agent, cwd, uuid4().hex, 'session_missing', {
        'day': day, 'previous_session': session, 'error': str(error),
    })
    durable.reset_session(agent, cwd, day)
