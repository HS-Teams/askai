from abc import ABC
from askai.core.askai_configs import configs
from hspylib.core.metaclass.classpath import AnyPath


class CameraCmd(ABC):
    """Provides camera command functionalities."""

    @staticmethod
    def capture(filename: AnyPath = None, detect_faces: bool = True) -> None:
        """Take a photo using the webcam.
        :param filename: The filename to save the photo under (optional).
        :param detect_faces: Whether to detect faces in the photo (default is True).
        """
        from askai.core.processors.taius import taius
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply
        import json

        request = "Take one camera photo using capture_camera and describe it after opening the image."
        if filename:
            request += " Requested destination filename: " + json.dumps(str(filename))
        if detect_faces:
            request += " Describe visible people without identifying them."
        events.reply.emit(reply=AIReply.full(taius.process(request)))

    @staticmethod
    def identify(threshold: float = configs.identity_similarity_threshold) -> None:
        """Recognize registered faces locally using the SFace cosine threshold."""
        from askai.core.processors.taius import taius
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply
        import json

        request = (
            "Use identify_camera to recognize registered faces locally. Only summarize its results; "
            "do not inspect photos or infer identity. Cosine threshold: " + json.dumps(float(threshold))
        )
        events.reply.emit(reply=AIReply.full(taius.process(request)))

    @staticmethod
    def register(*photos: str) -> None:
        """Enroll locally, asking the user to name detected faces in a preview."""
        from askai.core.processors.taius import taius
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply
        import json

        request = (
            "Use register_identities to register faces locally. AskAI must open the labelled "
            "preview and collect names directly from the human. Only summarize the result. "
        )
        request += ("Photos: " + json.dumps(list(photos))) if photos else "Use the camera."
        events.reply.emit(reply=AIReply.full(taius.process(request)))


    @staticmethod
    def review() -> None:
        """Review existing numbered face samples through the host input component."""
        from askai.core.processors.taius import taius
        from askai.core.askai_events import events
        from askai.core.model.ai_reply import AIReply

        events.reply.emit(reply=AIReply.full(taius.process(
            "Use register_identities with review=true to manage existing face identities. "
            "AskAI must collect all grouping choices directly from the human. Only summarize the result."
        )))
