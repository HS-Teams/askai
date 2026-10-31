"""Generate a complete, validated final answer; never repair malformed output."""

from pydantic import ValidationError
from askai.core.engine.inference import Inference
from askai.core.model.refined_response import RefinedResponse
from askai.exception.exceptions import InaccurateResponse


def refine_response(
    model: Inference, template: str, *, assistive_instructions: str = "", search_instructions: str = "", **arguments
) -> str:
    instructions = template.format(
        assistive_instructions=assistive_instructions, search_instructions=search_instructions, **arguments
    )
    raw = model.complete(
        [{"role": "system", "content": instructions}],
        temperature=0.0,
        schema=RefinedResponse.model_json_schema(),
    )
    try:
        return RefinedResponse.model_validate_json(raw).final_answer
    except (ValidationError, TypeError) as error:
        raise InaccurateResponse(
            "The refiner returned an invalid final-answer payload"
        ) from error
