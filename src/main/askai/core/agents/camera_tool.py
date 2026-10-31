"""Host camera tool: AskAI owns consent, camera countdown and sound effects."""
import json
from askai.core.agents.contracts import AgentEvent
from askai.core.permissions.grants import grants

CAMERA_TOOL = {
    "type": "function", "name": "capture_camera",
    "description": "Take one camera photo with user confirmation and a visible audible countdown. Open the returned target with view_image before describing it.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
}


def capture_camera(params, interact, emit, cancelled):
    if params.get("arguments") != {}:
        raise ValueError("capture_camera does not accept arguments")
    allowed = not cancelled.is_set() and grants.authorize(
        ["camera.capture.local", "vision.share.agent"],
        "Allow AskAI to take one camera photo and share it with the current agent for visual analysis?", interact,
    )
    result = capture_local(params, emit, cancelled) if allowed else {"status": "cancelled", "operation": "capture_camera"}
    return {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps(result)}]}


def capture_local(params, emit, cancelled):
    """Capture after the calling operation has authorized its complete grant set."""
    if cancelled.is_set():
        return {"status": "cancelled", "operation": "capture_camera"}
    emit(AgentEvent("camera_started", params["threadId"], params["turnId"]))
    try:
        from askai.core.component.multimedia.camera import camera
        target = camera.capture_frame()
        return {"status": "completed", "operation": "capture_camera", "target": target}
    finally:
        emit(AgentEvent("camera_finished", params["threadId"], params["turnId"]))
