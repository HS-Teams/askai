"""Authorize background gestures and publish recognition through the AskAI bus."""
from askai.gestures.session import authorize
from askai.gestures.background import launch

MESSAGES = {
    'inactive': 'No control hand recognized for more than five seconds. Stopping gesture control.',
    'scroll_top': 'Scroll to top requested.',
    'scroll_bottom': 'Scroll to bottom requested.',
    'scroll_start': 'Scroll mode enabled. Repeat the two-finger gesture to disable it.',
    'scroll_stop': 'Scroll mode disabled.',
    'scroll_up': 'Scrolling up.',
    'scroll_down': 'Scrolling down.', 
    'started': 'Gesture control started.',
    'pinch': 'Pinch recognized: mouse button held.',
    'release': 'Pinch released.',
    'escape': 'Open palm recognized: Escape sent.',
    'exit': 'Rock hand recognized: stopping gesture control.',
    'double_click': 'Thumbs up recognized: double-click sent.',
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

    if not authorize(grants, taius.interact):
        return {'status': 'cancelled'}
    labels = {text: msg.t(text) for text in Preview.LABELS}

    def notify(kind):
        from askai.gestures.sfx import play_init, play_quit, play_ptt
        if kind == 'started':
            play_init()
        elif kind == 'exit':
            play_quit()
        if kind == 'voice':
            play_ptt()
            events.voice_input.emit()
            return
        message = MESSAGES[kind]
        events.reply.emit(reply=AIReply.system(message))

    return launch(camera_index, askai_data_dir(), labels, notify)
