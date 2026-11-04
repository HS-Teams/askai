"""Ask for clarification without leaving the active agent turn."""
import json
from jsonschema import validate

USER_INPUT_METHOD = 'item/tool/requestUserInput'
CLARIFICATION_TOOL = {
    'type': 'function', 'name': 'askai_clarify',
    'description': (
        'Pause the current task to resolve ambiguity or a missing user preference. '
        'Ask 1-3 concise questions, with 2-3 distinct options when useful. '
        'Users can select an option or write their own answer. Continue the same task '
        'afterward; never restart or replay completed actions. Ask only when the answer '
        'materially affects the result. This asks questions, never grants permissions.'
    ),
    'inputSchema': {
        'type': 'object', 'additionalProperties': False, 'required': ['questions'],
        'properties': {'questions': {
            'type': 'array', 'minItems': 1, 'maxItems': 3,
            'items': {'type': 'object', 'additionalProperties': False,
                     'required': ['id', 'question'], 'properties': {
                'id': {'type': 'string', 'minLength': 1},
                'question': {'type': 'string', 'minLength': 1},
                'options': {'type': 'array', 'minItems': 2, 'maxItems': 3,
                            'items': {'type': 'object', 'additionalProperties': False,
                                      'required': ['label', 'description'], 'properties': {
                                'label': {'type': 'string', 'minLength': 1},
                                'description': {'type': 'string'}}}},
            }},
        }},
    },
}


def selected_answer(question, value):
    value = value.strip()
    options = question.get('options') or []
    if value.isdecimal() and 1 <= int(value) <= len(options):
        return options[int(value) - 1]['label']
    return value


def clarify(params, interact, emit, cancelled):
    arguments = params.get('arguments')
    validate(arguments, CLARIFICATION_TOOL['inputSchema'])
    ids = [question['id'] for question in arguments['questions']]
    if len(ids) != len(set(ids)):
        raise ValueError('Clarification question IDs must be unique')
    response = {'answers': {}}
    if not cancelled.is_set():
        response = interact(USER_INPUT_METHOD, arguments)
    if cancelled.is_set():
        response = {'answers': {}}
    return {'success': True, 'contentItems': [
        {'type': 'inputText', 'text': json.dumps(response, ensure_ascii=False)}]}
