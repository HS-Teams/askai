"""Live command results and bounded diagnostic logs for the current AskAI app."""
from contextlib import redirect_stdout
from io import StringIO
import sys
from threading import RLock, get_ident
from askai.core.support.communication import communication, SESSION_MESSAGES


MAX_RESULTS = 10
MAX_OUTPUT = 16000
_console_lock = RLock()


class _CommandOutput:
    """Observe this command's console writes while keeping prompts visible live."""
    def __init__(self, target, collector=None):
        self.target = target
        self.thread = get_ident()
        self.text = StringIO()
        self.length = 0
        self.collector = collector if collector is not None else self

    def write(self, text):
        if get_ident() == self.thread:
            remaining = max(0, MAX_OUTPUT - self.collector.length)
            self.collector.text.write(text[:remaining])
            self.collector.length += len(text)
        communication.publish('command.output', {'text': text},
                              screen=lambda: self.target.write(text), remember=False, record=False)
        return len(text)

    def __getattr__(self, name):
        return getattr(self.target, name)


def record_result(result):
    communication.publish('command.result', result)
    return result


def recent_results(command=''):
    results = [event['payload'] for event in communication.recent('command.result', limit=SESSION_MESSAGES)]
    return [result for result in results[-MAX_RESULTS:] if not command or result['command'] == command]


def command_diagnostics(command=''):
    results = [event['payload'] for event in communication.recent('command.result', limit=SESSION_MESSAGES)]
    entries = [{'command': result['command'], 'error': result['error']}
               for result in results if result['status'] == 'failed'
               and (not command or result['command'] == command)][-MAX_RESULTS:]
    return {'source': 'current_process_command_log', 'entries': entries,
            'delivery_errors': [{'event_id': event['id'], 'kind': event['kind'],
                                 'errors': event['delivery_errors']}
                                for event in communication.recent(limit=SESSION_MESSAGES)
                                if event['delivery_errors']],
            'message': 'Diagnostic evidence only; use live state for current values.'}


def execute_command(arguments, *, raise_errors=False):
    from askai.core.commander.commander import ask_commander
    from askai.cli import output as cli_output

    result = {'command': arguments[0], 'arguments': arguments[1:], 'status': 'completed'}
    console = cli_output.console
    failure = None
    with _console_lock:
        original = console.file
        captured = _CommandOutput(original)
        console.file = captured
        try:
            with redirect_stdout(_CommandOutput(sys.stdout, captured)):
                value = ask_commander(arguments, standalone_mode=False)
            if isinstance(value, dict):
                result['data'] = value
                if value.get('status') == 'failed':
                    result.update(status='failed', error=value['error'])
        except Exception as error:
            failure = error
            result.update(status='failed', error=str(error), error_type=type(error).__name__)
        finally:
            console.file = original
    result['output'] = captured.text.getvalue()
    result['output_truncated'] = captured.length > MAX_OUTPUT
    record_result(result)
    if failure is not None and raise_errors:
        raise failure
    return result


def current_state(command=''):
    if command and command != 'voices':
        return {'source': 'current_app', 'results': recent_results(command)}
    from askai.core.askai_configs import configs
    from askai.core.support.shared_instances import shared

    speech = shared.speech.tts
    provider = getattr(speech, 'voice_engine', speech)
    state = {
        'source': 'current_app',
        'engine': configs.engine,
        'model': shared.engine.ai_model_name(),
        'communications': communication.recent(),
        'tts': {'provider': getattr(speech, 'provider_name', configs.tts_engine),
                'model': provider.model_name, 'voice': provider.voice,
                'active_model': speech.model_name, 'active_voice': speech.voice},
        'stt': {'provider': configs.stt_engine, 'language': configs.stt_language.idiom},
        'results': recent_results(command),
    }
    if command == 'voices':
        state['tts']['voices'] = [{'index': index, 'name': voice}
                                  for index, voice in enumerate(provider.voices())]
        state['tts']['index_base'] = 0
    return state
