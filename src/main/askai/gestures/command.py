"""Authorize background gestures and publish recognition through the AskAI bus."""
from askai.gestures.session import authorize
from askai.gestures.background import launch

MESSAGES = {
    'inactive': 'Gesture control paused. Keep your right hand visible above your waist for three seconds to resume.',
    'waist_missing': 'Your hips could not be detected with enough confidence. Gesture commands are blocked. Adjust your body position so your shoulders and hips are visible to the camera.',
    'resumed': 'Gesture control resumed.',
    'scroll_top': 'Scroll to top requested.',
    'scroll_bottom': 'Scroll to bottom requested.',
    'scroll_start': 'Scroll mode enabled. Repeat the two-finger gesture to disable it.',
    'scroll_stop': 'Scroll mode disabled.',
    'scroll_up': 'Scrolling up.',
    'scroll_down': 'Scrolling down.', 
    'started': 'Gesture control started.',
    'pinch': 'Pinch recognized: mouse button held.',
    'release': 'Pinch released.',
    'escape': 'Heavy metal gesture recognized: Escape sent.',
    'double_click': 'Open palm recognized: double-click sent.',
    'exit': 'Thumbs up recognized: stopping gesture control.',
    'stopped': 'Gesture control stopped.',
    'failed': 'Gesture control failed. See logs/gestures.log for details.',
}


def start(camera_index=0):
    from askai.core.permissions.grants import grants
    from askai.core.processors.taius import taius
    from askai.core.support.app_paths import askai_data_dir
    from askai.core.askai_messages import msg
    from askai.core.askai_events import events
    from askai.core.model.ai_reply import AIReply
    from askai.gestures.preview import Preview
    from askai.gestures.sfx import play_init, play_quit, play_ptt

    if not authorize(grants, taius.interact):
        return {'status': 'cancelled'}
    labels = {text: msg.t(text) for text in Preview.LABELS}

    def notify(kind):
        if kind == 'exit':
            play_quit()
        if kind == 'voice':
            play_ptt()
            events.voice_input.emit()
            return
        message = MESSAGES[kind]
        events.reply.emit(reply=AIReply.system(message))

    from askai.cli.gestures_loading import gestures_loading
    from askai.core.support.text_formatter import text_formatter

    with gestures_loading(text_formatter.console, msg.t) as update:
        result = launch(camera_index, askai_data_dir(), labels, notify,
                        wait_ready=True, on_progress=update)
    play_init()
    text_formatter.commander_print(msg.t(MESSAGES['started']))
    return result
