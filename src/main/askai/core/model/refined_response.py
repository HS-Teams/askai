"""Validated output contract for the answer refiner."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RefinedResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    final_answer: str = Field(
        description="Only the final user-facing answer, preserving its Markdown. No editing report or explanation."
    )

    @field_validator("final_answer")
    @classmethod
    def require_nonblank_answer(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("The final answer must not be blank")
        return value
