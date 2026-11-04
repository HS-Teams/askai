"""Authorize background gestures and publish recognition through the AskAI bus."""
from askai.gestures.session import authorize
from askai.gestures.background import launch

MESSAGES = {
    'ptt_paused': 'Gesture control paused during voice capture. After speaking, keep your right hand visible above your waist for 2.5 seconds to resume.',
    'inactive': 'Gesture control paused. Keep your right hand visible above your waist for 2.5 seconds to resume.',
    'inactivity_warning': 'O detector de gestos irá ser desativado em 15 segundos',
    'waist_missing': 'Hips not detected reliably. Show your shoulders and hips to the camera to enable gestures.',
    'resumed': 'Gesture control resumed.',
    'scroll_start': 'Scroll mode enabled. Other gestures are blocked.',
    'scroll_stop': 'Scroll mode disabled. Gestures resumed.',
    'scroll_up': 'Scrolling up.',
    'scroll_down': 'Scrolling down.', 
    'started': 'Gesture control started.',
    'pinch': 'Pinch recognized: mouse button held.',
    'release': 'Pinch released.',
    'abort': 'Heavy Metal gesture recognized: abort requested for the current AskAI operation.',
    'double_click': 'Open palm recognized: double-click sent.',
    'exit': 'Thumbs up recognized: stopping gesture control.',
    'stopped': 'Gesture control stopped.',
    'failed': 'Gesture control failed. See logs/gestures.log for details.',
}


def abort_current_request():
    from askai.core.support.shared_instances import shared
    from askai.core.askai_events import events

    shared.speech.cancel_output()
    processor = shared.mode.processor
    if hasattr(processor, 'cancel'):
        processor.cancel()
    events.abort.emit(message='User interrupted [Heavy Metal]')


def start(camera_index=0):
    from askai.core.askai_configs import configs
    from askai.core.permissions.grants import grants
    from askai.core.processors.taius import taius
    from askai.core.support.app_paths import askai_data_dir
    from askai.core.askai_messages import msg
    from askai.core.askai_events import events
    from askai.core.model.ai_reply import AIReply
    from askai.gestures.preview import Preview
    from askai.gestures.sfx import play_init, play_quit, play_ptt, play_scroll_up, play_scroll_down, play_abort

    if not authorize(grants, taius.interact):
        return {'status': 'cancelled'}
    labels = {text: msg.t(text) for text in Preview.LABELS}

    def notify(kind):
        if kind == 'abort':
            abort_current_request()
            play_abort()
        if kind == 'scroll_up':
            play_scroll_up()
        elif kind == 'scroll_down':
            play_scroll_down()
        if kind == 'exit':
            play_quit()
        if kind == 'voice':
            play_ptt()
            events.voice_input.emit()
            return
        message = MESSAGES[kind]
        events.reply.emit(reply=AIReply.system(message))

    from askai.cli.gestures_loading import gestures_loading
    from askai.cli import output as cli_output

    with gestures_loading(cli_output.console, msg.t) as update:
        result = launch(camera_index, askai_data_dir(), labels, notify,
                        wait_ready=True, on_progress=update, sfx_muted=configs.is_sfx_muted)
    play_init()
    cli_output.render_command(msg.t(MESSAGES['started']))
    return result
