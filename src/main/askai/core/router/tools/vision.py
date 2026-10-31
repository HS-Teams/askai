from askai.core.askai_events import events
from askai.core.askai_messages import msg
from askai.core.component.cache_service import PICTURE_DIR
from askai.core.engine.ai_vision import AIVision
from askai.core.model.ai_reply import AIReply
from askai.core.model.image_result import ImageResult
from askai.core.model.screenshot_result import ScreenshotResult
from askai.core.router.evaluation import resolve_x_refs
from askai.core.support.shared_instances import shared
from hspylib.core.config.path_object import PathObject
from hspylib.core.enums.enumeration import Enumeration
from hspylib.core.metaclass.classpath import AnyPath
from PIL import Image
from string import Template
from textwrap import indent
from transformers import BlipForConditionalGeneration, BlipProcessor
from typing import Literal

import os
import json
import torch

SCREENSHOT_TEMPLATE: Template = Template(
    """\

>   Screenshot `${image_path}`:

${image_caption}

"""
)


class HFModel(Enumeration):
    """Available Hugging Face models"""

    # fmt: off
    SF_BLIP_BASE = "Salesforce/blip-image-captioning-base"
    SF_BLIP_LARGE = "Salesforce/blip-image-captioning-large"

    # fmt: on

    @staticmethod
    def default() -> "HFModel":
        """Return the default HF model."""
        return HFModel.SF_BLIP_BASE


def offline_captioner(path_name: AnyPath) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    """

    caption: str = "Not available"

    posix_path: PathObject = PathObject.of(path_name)
    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        events.reply.emit(reply=AIReply.full(msg.describe_image(posix_path)))
        # Use GPU if it's available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        image = Image.open(str(posix_path)).convert("RGB")
        model_id: str = HFModel.default().value
        match model_id.casefold():
            case model if "blip-" in model:
                model = BlipForConditionalGeneration.from_pretrained(model_id).to(device)
                processor = BlipProcessor.from_pretrained(model_id)
            case _:
                raise ValueError(f"Unsupported model: '{model_id}'")
        inputs = processor(images=image, return_tensors="pt").to(device)
        outputs = model.generate(**inputs)
        caption = processor.decode(outputs[0], skip_special_tokens=True)
        caption = caption.title() if caption else "I could not caption the image"

    return json.dumps({"env_description": caption})


def image_captioner(
    path_name: AnyPath,
    load_dir: AnyPath | None = None,
    query: str | None = None,
    image_type: Literal["photo", "screenshot"] = "photo",
) -> str:
    """This tool is used to describe an image.
    :param path_name: The path of the image to describe.
    :param load_dir: Optional directory path for loading related resources.
    :param query: Optional query about the photo taken.
    :param image_type: The type of the image to be captioned; one of 'photo' or 'screenshot'.
    :return: A string containing the description of the image, or None if the description could not be generated.
    """

    image_caption: str = "Unavailable"
    posix_path: PathObject = PathObject.of(path_name)

    if not posix_path.exists:
        # Attempt to resolve cross-references
        if history := str(shared.context.flat("HISTORY") or ""):
            if (x_referenced := resolve_x_refs(path_name, history)) and x_referenced != shared.UNCERTAIN_ID:
                x_ref_path: PathObject = PathObject.of(x_referenced)
                posix_path: PathObject = x_ref_path if x_ref_path.exists else posix_path

    if posix_path.exists:
        if os.environ.get("ASKAI_APP", None) is None:
            return offline_captioner(str(posix_path))
        events.reply.emit(reply=AIReply.full(msg.describe_image(posix_path)))
        vision: AIVision = shared.engine.vision()
        image_caption = vision.caption(
            posix_path.filename, load_dir or posix_path.abs_dir or PICTURE_DIR, query, image_type
        )

    return image_caption


def parse_image_caption(image_caption: str | None) -> list[str]:
    """Parse the given image caption.
    :param image_caption: The caption to parse.
    :return: The parsed caption as a string.
    """
    if image_caption:
        events.reply.emit(reply=AIReply.full(msg.parsing_caption()))
        result: ImageResult = ImageResult.of(image_caption)
        ln: str = os.linesep
        # fmt: off
        people_desc = [
            f"- **People:** `({result.people_count})`",
            indent(f"- {'- '.join([f'`{ppl}{ln}`' + ln for ppl in result.people_description])}", "    "),
        ] if result.people_count and result.people_description else []
        user_response_desc = [f"- **Answer**: `{result.user_response}`"] if result.user_response else []
        objects_desc = [f"- **Objects:** `{', '.join(result.main_objects)}`"] if result.main_objects else []
        return [f"- **Description:** `{result.env_description}`"] + objects_desc + people_desc + user_response_desc
        # fmt: on

    return [msg.no_caption()]


def parse_screenshot_caption(screenshot_caption: str) -> list[str]:
    """Parse the given screenshot caption.
    :param screenshot_caption: The caption to parse.
    :return: The parsed caption as a string.
    """
    if screenshot_caption:
        events.reply.emit(reply=AIReply.full(msg.parsing_caption()))
        result: ScreenshotResult = ScreenshotResult.of(screenshot_caption)
        ln: str = os.linesep
        apps_desc: list[str] = []
        docs_desc: list[str] = []
        web_pages: list[str] = []
        user_response_desc: list[str] = []
        if result.open_applications:
            apps_desc = [
                f"- **Applications:**",
                indent(f"- {'- '.join([f'`{app}{ln}`' + ln for app in result.open_applications])}", "    "),
            ]
        if result.open_documents:
            docs_desc = [
                f"- **Documents:**",
                indent(f"- {'- '.join([f'`{app}{ln}`' + ln for app in result.open_documents])}", "    "),
            ]
        if result.web_pages:
            web_pages = [
                f"- **WebPages:**",
                indent(f"- {'- '.join([f'`{app}{ln}`' + ln for app in result.web_pages])}", "    "),
            ]
        if result.user_response:
            user_response_desc = [f"- **Answer**: `{result.user_response}`"]
        # fmt: off
        return apps_desc + docs_desc + web_pages + user_response_desc
        # fmt: on

    return [msg.no_caption()]


def capture_screenshot(
    path_name: AnyPath | None = None, save_dir: AnyPath | None = None, query: str | None = None
) -> str:
    """Capture a screenshot and save it to the specified path.
    :param path_name: Optional path name of the captured screenshot.
    :param save_dir: Optional directory to save the screenshot.
    :param query: Optional query about the screenshot taken.
    :return: The path to the saved screenshot.
    """

    from askai.core.processors.taius import taius
    import json

    request = "Capture the screen using the AskAI capture_screenshot tool and analyze the saved image."
    if path_name or save_dir:
        request += " Requested output location: " + json.dumps({"filename": str(path_name or ""), "directory": str(save_dir or "")})
    if query:
        request += " User question about the screenshot: " + json.dumps(query)
    return taius.process(request)
