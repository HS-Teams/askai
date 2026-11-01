"""Retire the runtime session before forgetting its local resume pointer."""


def reset_saved_session(backend, durable, agent, cwd, day, session=None):
    session = session or (durable.session(agent, cwd, day) if durable else None)
    if session:
        backend.archive(session)
    if durable:
        durable.reset_session(agent, cwd, day)
