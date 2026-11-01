"""Discover AskAI help on demand and request commands in the current app."""
import json

from askai.core.commander.agent_commands import queue_command
from askai.core.commander.command_results import (
    command_diagnostics, current_state, execute_command, record_result,
)


# These callbacks invoke inference or change the active session/router.
DEFERRED_COMMANDS = {'camera', 'dictate', 'summarize', 'session', 'mode', 'usage', 'engine', 'model', 'gestures'}


COMMAND_TOOL = {
    'type': 'function',
    'name': 'askai_command',
    'description': (
        'Use AskAI commands in the current app, never by launching another AskAI process. '
        'Get help on demand with action=help (omit command for the catalogue). '
        'For action=execute, use a registered command name and separate argument tokens. '
        'Use action=state for live app state and recent structured command results; '
        'command=voices includes the current zero-based voice catalogue. '
        'Execution returns structured results and output. Commands requiring another agent '
        'turn are queued; report those as queued, not completed. '
        'After a failure, use action=diagnostics to inspect command logs before claiming access is unavailable. '
        'Use only for user-requested commands; existing permissions still apply.'
    ),
    'inputSchema': {
        'type': 'object',
        'properties': {
            'action': {'type': 'string', 'enum': ['help', 'state', 'execute', 'diagnostics']},
            'command': {'type': 'string', 'description': 'Canonical command name, optionally prefixed with /.'},
            'arguments': {'type': 'array', 'items': {'type': 'string'}},
        },
        'required': ['action'],
        'additionalProperties': False,
    },
}


def askai_command(params, interact, emit, cancelled):
    arguments = params.get('arguments')
    if not isinstance(arguments, dict) or set(arguments) - {'action', 'command', 'arguments'}:
        raise ValueError('Invalid AskAI command request')
    action = arguments.get('action')
    command = arguments.get('command', '')
    tokens = arguments.get('arguments', [])
    if not isinstance(command, str) or not isinstance(tokens, list) or any(not isinstance(t, str) for t in tokens):
        raise ValueError('Command and arguments must be strings')
    command = command.removeprefix('/')
    if cancelled.is_set():
        result = {'status': 'cancelled'}
    elif action == 'help':
        from askai.core.commander.commander import commander_help
        if tokens:
            raise ValueError('Help accepts a command name without arguments')
        result = {'status': 'completed', 'help': commander_help(command or None)}
    elif action == 'execute':
        from askai.core.commander.commander import ask_commander
        if command not in ask_commander.commands:
            raise ValueError('Unknown AskAI command; request help first')
        _check_permissions(command, tokens)
        if command in DEFERRED_COMMANDS:
            queue_command(command, tokens, cancelled)
            result = {'status': 'queued', 'command': command, 'arguments': tokens,
                      'message': 'Runs after this turn. Query action=state on the next turn for its result; do not repeat the command.'}
        else:
            result = execute_command([command, *tokens])
    elif action in {'state', 'diagnostics'}:
        if tokens:
            raise ValueError('State and diagnostics accept a command name without arguments')
        try:
            data = current_state(command) if action == 'state' else command_diagnostics(command)
            result = {'status': 'completed', 'data': data}
        except Exception as error:
            result = record_result({'status': 'failed', 'command': command or 'state',
                                    'error': str(error), 'error_type': type(error).__name__})
    else:
        raise ValueError('Action must be help, state, execute or diagnostics')
    return {'success': result['status'] != 'failed',
            'contentItems': [{'type': 'inputText', 'text': json.dumps(result, default=str)}]}


def _check_permissions(command, arguments):
    # Agents must not bypass denied capabilities by changing the grant settings.
    arguments = [argument for argument in arguments if argument != '--']
    operation = arguments[0].casefold() if arguments else ''
    if command == 'grants' and operation in {'set', 'reset'}:
        raise ValueError('Permission changes must be made directly by the user in AskAI')
    if command == 'settings' and arguments:
        if operation == 'reset':
            raise ValueError('Settings reset must be requested directly in AskAI because it resets permissions')
        if operation == 'set':
            name = arguments[1] if len(arguments) > 1 else ''
            if name.isdecimal() or name.startswith('askai.grants.'):
                raise ValueError('Agent settings changes require a non-permission setting name')
