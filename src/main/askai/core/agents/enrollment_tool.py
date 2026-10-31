"""AskAI owns enrollment consent and human labels; the agent sees only results."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from askai.core.agents.contracts import AgentEvent
from askai.core.agents.elicitation import INPUT_FORM_METHOD, validate_reply
from askai.core.permissions.grants import grants
from askai.core.component.faces.selections import MAX_IDENTITY_NAME, FaceAction, FaceSelection

ENROLLMENT_TOOL = {
    "type": "function", "name": "register_identities",
    "description": (
        "Register identities locally from photos or one camera capture. AskAI confirms access, detects and numbers "
        "faces, opens a numbered preview and asks the human to create, merge, replace or skip samples. Omit photos to use the camera; review=true manages existing samples without capture. "
        "Only summarize the returned result; never guess names or repeat enrollment during review."
    ),
    "inputSchema": {
        "type": "object", "properties": {
            "review": {"type": "boolean", "description": "Review existing numbered face samples without capture."},
            "photos": {"type": "array", "items": {"type": "string", "minLength": 1}, "minItems": 1},
        }, "additionalProperties": False,
    },
}


def _form(interact, message, properties=None):
    request = {
        "serverName": "AskAI", "mode": "form", "message": message,
        "requestedSchema": {"type": "object", "properties": properties or {}, "additionalProperties": False},
    }
    decision = interact(INPUT_FORM_METHOD, request)
    validate_reply(request, decision)
    return decision.get("content", {}) if decision["action"] == "accept" else None


def _services():
    from askai.core.component.cache_service import FACE_DIR, PICTURE_DIR
    from askai.core.component.faces.service import face_services
    from askai.core.askai_configs import configs
    from askai.core.component.multimedia.camera import camera
    from askai.core.component.identity_enrollment import IdentityEnrollment
    from askai.core.capabilities.desktop import DesktopCapabilities

    models, index, _ = face_services()
    captioner = None
    if configs.identity_caption_enabled:
        from askai.core.router.tools.vision import offline_captioner
        captioner = offline_captioner
    return (
        IdentityEnrollment(models, index, Path(FACE_DIR), captioner),
        camera, DesktopCapabilities(Path(PICTURE_DIR)), Path(PICTURE_DIR),
    )


def register_identities(params, interact, emit, cancelled):
    arguments = params.get("arguments")
    from jsonschema import validate

    validate(arguments, ENROLLMENT_TOOL["inputSchema"])
    photos = arguments.get("photos")
    review = arguments.get("review", False)
    if review and photos:
        raise ValueError("Review cannot be combined with new photos")
    message = (
        "Allow AskAI to read these photos, open numbered face previews and store the faces you name locally?\n"
        + "\n".join(photos)
        if photos else
        "Allow AskAI to capture a camera photo, open a numbered face preview and store the faces you name locally?"
    )
    if review:
        message = "Allow AskAI to open a numbered preview of registered faces for local identity management?"
    required = ["identities.read.local"]
    if not review:
        required.append("images.read.local" if photos else "camera.capture.local")
    if cancelled.is_set() or not grants.authorize(required, message, interact) or cancelled.is_set():
        return _result("cancelled")
    if photos:
        photos = [_photo_path(photo) for photo in photos]
    enrollment, camera, desktop, directory = _services()
    if not photos and not review:
        emit(AgentEvent("camera_started", params["threadId"], params["turnId"]))
        try:
            photos = [camera.capture_frame()]
        finally:
            emit(AgentEvent("camera_finished", params["threadId"], params["turnId"]))
    directory.mkdir(parents=True, exist_ok=True)
    selections = []
    detected_faces = 0
    with TemporaryDirectory(prefix="identity-enrollment-", dir=directory) as scratch:
        for source in ([None] if review else photos):
            if cancelled.is_set():
                return _result("cancelled")
            emit(AgentEvent("tool_progress", params["threadId"], params["turnId"],
                            data={"message": "Detecting and encoding faces locally…"}))
            prepared = enrollment.review(Path(scratch)) if review else enrollment.prepare(source, Path(scratch))
            detected_faces += len(prepared.faces)
            if not prepared.faces:
                continue
            if cancelled.is_set():
                return _result("cancelled")
            desktop.open_path(str(prepared.preview))
            fields = {}
            for face in prepared.faces:
                fields[f"action_{face.label}"] = {
                    "type": "string", "title": f"Face {face.label}: action (blank = Skip)",
                    "oneOf": [
                        {"const": action.value, "title": title}
                        for action, title in (
                            (FaceAction.SKIP, "Skip — do not select this face"),
                            (FaceAction.NEW, "New identity"),
                            (FaceAction.MERGE, "Merge — keep existing samples"),
                            (FaceAction.REPLACE, "Replace — replace all samples of the target identity"),
                        )
                    ],
                }
                fields[f"face_{face.label}"] = {
                    "type": "string", "title": f"Face {face.label}: target name (except Skip)",
                    "maxLength": MAX_IDENTITY_NAME, "pattern": r"^[^\x00-\x1f\x7f]*$",
                }
                if face.current_name:
                    fields[f"face_{face.label}"]["description"] = f"Current identity: `{face.current_name}`"
            identities = enrollment.identities()
            existing = "\n".join(f"- `{item['name']}`: {item['samples']}" for item in identities)
            message = (
                "Choose an action and name for each numbered face. Merge adds the selected face to an "
                "identity. Replace removes all current samples of that identity, including unselected ones, from recognition. "
                "Photo files are preserved. Blank action means Skip. Cancel discards the entire batch.\n" + existing
            )
            while True:
                names = _form(interact, message, fields)
                if names is None or cancelled.is_set():
                    return _result("cancelled")
                choices = [FaceSelection(
                    face, FaceAction(names.get(f"action_{face.label}", "skip")), names.get(f"face_{face.label}", "")
                ) for face in prepared.faces]
                try:
                    enrollment.plan(selections + choices)
                    selections.extend(choices)
                    break
                except ValueError as error:
                    message = "Invalid identity choice: " + str(error) + "\n" + message
        planned = enrollment.plan(selections)
        if planned:
            summary = "\n".join(f"- {choice.action.value}: face {choice.face.label} -> `{choice.name}`" for choice in planned)
            permissions = [
                f"identities.{'create' if choice.action == FaceAction.NEW else choice.action.value}.local"
                for choice in planned
            ]
            if not grants.authorize(permissions, "Apply these identity changes? Replace removes the target's old samples from "
                                    "recognition, including unselected samples; all photo files are preserved.\n" + summary,
                                    interact):
                return _result("cancelled")
        if cancelled.is_set():
            return _result("cancelled")
        registered = enrollment.save(selections)
    return _result("completed", registered=registered, detected_faces=detected_faces)


def _photo_path(path):
    source = Path(path).expanduser()
    if not source.is_absolute() or not source.is_file():
        raise ValueError("Each photo must be an existing absolute file path")
    return str(source.resolve(strict=True))


def _result(status, **details):
    return {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps({
        "operation": "register_identities", "status": status, **details,
    })}]}
