"""Local image identification; the agent only interprets captured evidence."""
import json
import math
import cv2

from askai.core.agents.camera_tool import capture_local
from askai.core.permissions.grants import grants

IDENTIFICATION_TOOL = {
    "type": "function", "name": "identify_camera",
    "description": (
        "Confirm camera use, capture with countdown and recognize registered faces locally with YuNet and SFace. "
        "Only summarize the returned results. Do not open photos or infer identities yourself."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {"threshold": {"type": "number", "minimum": -1, "maximum": 1}},
        "additionalProperties": False,
    },
}


def identify_camera(params, interact, emit, cancelled):
    arguments = params.get("arguments")
    if not isinstance(arguments, dict) or arguments.keys() - {"threshold"}:
        raise ValueError("identify_camera accepts only threshold")
    from askai.core.askai_configs import configs

    threshold = arguments.get("threshold", configs.identity_similarity_threshold)
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or not math.isfinite(threshold) or not -1 <= threshold <= 1:
        raise ValueError("threshold must be a finite number between -1 and 1")

    allowed = not cancelled.is_set() and grants.authorize(
        ["camera.capture.local", "identities.read.local"],
        "Allow AskAI to take a camera photo and recognize registered faces locally? Only recognition results are shared with the agent.",
        interact,
    )
    result = capture_local(params, emit, cancelled) if allowed else {"status": "cancelled"}
    result["operation"] = "identify_camera"
    if result["status"] == "completed" and not cancelled.is_set():
        from askai.core.component.faces.service import face_services

        models, index, _ = face_services()
        photo = cv2.imread(result["target"])
        faces = models.detect(photo)
        result.update(
            threshold=threshold,
            faces=index.match([face.vector for face in faces], threshold),
            method="local YuNet + SFace cosine similarity",
        )
    elif cancelled.is_set():
        result["status"] = "cancelled"
    result.pop("target", None)
    return {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps(result)}]}
