"""Native OpenAI image inference with Pydantic validation."""
import base64
import mimetypes
from pathlib import Path
from openai import OpenAI
from askai.core.askai_prompt import prompt
from askai.core.model.image_result import ImageResult
from askai.core.model.screenshot_result import ScreenshotResult


class OpenAIVision:
    def caption(self, filename, load_dir=None, query=None, image_type="photo") -> str:
        if image_type not in {"photo", "screenshot"}:
            raise ValueError(f"Invalid image type: {image_type}")
        schema = ImageResult if image_type == "photo" else ScreenshotResult
        path = Path(load_dir or ".") / filename
        mime = mimetypes.guess_type(path)[0] or "image/jpeg"
        image = base64.b64encode(path.read_bytes()).decode("ascii")
        instructions = prompt.read_prompt("img-caption" if image_type == "photo" else "ss-caption").format(question=query or "")
        response = OpenAI().chat.completions.create(model="gpt-4o-mini", messages=[{
            "role": "user", "content": [{"type": "text", "text": instructions},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image}"}}]}],
            response_format={"type": "json_schema", "json_schema": {
                "name": "image_caption", "schema": schema.model_json_schema()}})
        return str(schema.model_validate_json(response.choices[0].message.content).model_dump())
