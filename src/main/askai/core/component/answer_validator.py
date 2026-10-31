"""Strict assessment contract, independent of UI and provider SDKs."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from askai.core.model.acc_response import AccResponse
from askai.core.enums.acc_color import AccColor
from askai.exception.exceptions import InaccurateResponse


class Assessment(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    color: Literal["Black", "White", "Blue", "Green", "Yellow", "Red"]
    accuracy: float = Field(ge=0, le=100)
    reasoning: str
    tips: str


def validate_response(model, template: str, **arguments) -> AccResponse:
    raw = model.complete(
        [{"role": "user", "content": template.format(**arguments)}],
        temperature=0.0,
        schema=Assessment.model_json_schema(),
    )
    try:
        result = Assessment.model_validate_json(raw)
    except (ValidationError, TypeError) as error:
        raise InaccurateResponse(
            "The validator returned an invalid assessment"
        ) from error
    return AccResponse(
        AccColor.of_color(result.color), result.accuracy, result.reasoning, result.tips
    )
