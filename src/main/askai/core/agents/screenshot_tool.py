"""Host screenshot tool: capture in AskAI, visual analysis in the agent."""
import json
from askai.core.agents.contracts import AgentEvent
from askai.core.permissions.grants import grants

SCREENSHOT_TOOL = {
    'type': 'function', 'name': 'capture_screenshot',
    'description': 'Capture the current screen in AskAI after user confirmation and an audible countdown. Open the returned target with view_image before analyzing it.',
    'inputSchema': {'type': 'object', 'properties': {}, 'additionalProperties': False},
}


def capture_screenshot(params, interact, emit, cancelled):
    if params.get('arguments') != {}:
        raise ValueError('capture_screenshot does not accept arguments')
    allowed = not cancelled.is_set() and grants.authorize(
        ["screen.capture.local", "vision.share.agent"],
        "Allow AskAI to capture the current screen and share the screenshot with the current agent for visual analysis?",
        interact,
    )
    result = {'operation': 'capture_screenshot', 'status': 'cancelled'}
    if allowed and not cancelled.is_set():
        emit(AgentEvent('screenshot_started', params['threadId'], params['turnId']))
        try:
            from askai.core.component.multimedia.screenshot import capture_screenshot as capture
            if target := capture(cancelled):
                result.update(status='completed', target=target)
        finally:
            emit(AgentEvent('screenshot_finished', params['threadId'], params['turnId']))
    return {'success': True, 'contentItems': [{'type': 'inputText', 'text': json.dumps(result)}]}
