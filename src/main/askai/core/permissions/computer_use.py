"""Apply the computer-use grant to CUA consent requests, without answering forms."""
from askai.core.agents.elicitation import FORM_MODES
from askai.core.permissions.grants import GrantDenied, grants
from jsonschema import validate
import json


def computer_use_reply(params, interact, consent=None):
    schema = params.get('requestedSchema', {})
    if (params.get('serverName') != 'cua_repl'
            or params.get('mode', 'form') not in FORM_MODES
            or schema.get('type') != 'object'
            or schema.get('properties') != {}
            or schema.get('required')):
        return None
    validate({}, schema)
    key = consent_key(params)
    message = 'Use the computer'
    if details := params.get('message'):
        message += '\n\n' + details
    try:
        grants.pending(['computer.use'])
        if consent is not None and key in consent:
            accepted = consent[key]
        else:
            accepted = grants.authorize(['computer.use'], message, interact)
            if consent is not None:
                consent[key] = accepted
    except GrantDenied:
        if consent is not None:
            consent.pop(key, None)
        accepted = False
    return {'action': 'accept', 'content': {}} if accepted else {'action': 'decline'}


def consent_key(params):
    """Group the consent shown to the user, not the individual tool/RPC invocation.

    CUA identifies the requested application in its consent message. Keep that
    message exact: a different application or requested access must prompt again.
    Explicit scope fields are retained even when supplied in metadata.
    """
    scope = {
        'serverName': params['serverName'],
        'mode': 'form',
        'message': params.get('message', ''),
        'requestedSchema': params['requestedSchema'],
    }
    for source, values in (('request', params), ('metadata', params.get('_meta', {}))):
        if isinstance(values, dict):
            for field in ('scope', 'permissions', 'application', 'appId', 'bundleId', 'resource'):
                if field in values:
                    scope[source + '.' + field] = values[field]
    return json.dumps(scope, sort_keys=True, ensure_ascii=False)
