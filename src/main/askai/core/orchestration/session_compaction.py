"""Compact native agent context without replacing the journal or STM."""
from pathlib import Path
from askai.core.agents.contracts import AgentEvent
from askai.core.support.performance import timed


def compact_saved_session(backend, durable, agent, cwd, day, emit, *, session=None, model=None):
    session = session or durable.session(agent, cwd, day)
    if not session:
        return False
    revision, compacted = durable.compaction_revision(agent, cwd, session)
    if revision <= compacted:
        return False
    emit(AgentEvent('stage', session, data={'stage': 'compaction'}))
    with timed('session.compaction'):
        backend.compact(session, Path(cwd), model)
    durable.mark_compacted(agent, cwd, session, day, revision)
    return True
