"""Await native compaction without treating its immediate acknowledgement as completion."""
from time import monotonic
from askai.core.agents.contracts import AgentError


def compact_thread(transport, session, cwd, model=None, timeout=60):
    options = {'threadId': session, 'cwd': str(cwd), 'sandbox': 'read-only', 'approvalPolicy': 'never'}
    if model:
        options['model'] = model
    transport.request('thread/resume', options)
    transport.request('thread/compact/start', {'threadId': session})
    deadline = monotonic() + timeout
    turn_id = None
    compacted = False
    while monotonic() < deadline:
        message = transport.receive()
        if not message:
            continue
        params = message.get('params', {})
        if params.get('threadId') != session:
            continue
        method = message.get('method')
        if 'id' in message and method:
            transport.send({'id': message['id'], 'error': {'code': -32601, 'message': 'Compaction does not allow tool interactions'}})
            raise AgentError('Unexpected interaction during session compaction')
        if method == 'turn/started':
            turn_id = params['turn']['id']
        elif method == 'item/completed' and params.get('item', {}).get('type') == 'contextCompaction':
            if turn_id is None or params.get('turnId') == turn_id:
                turn_id = params.get('turnId', turn_id)
                compacted = True
        elif method == 'turn/completed':
            turn = params['turn']
            if turn_id is not None and turn.get('id') != turn_id:
                continue
            if turn.get('status') != 'completed':
                raise AgentError(f"Session compaction failed: {turn.get('error') or turn.get('status')}")
            if not compacted:
                raise AgentError('Codex completed without confirming context compaction')
            return
    raise AgentError('Session compaction timed out; completion was not confirmed')
