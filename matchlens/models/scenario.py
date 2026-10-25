import math
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from matchlens.config import SupportedDimension


class ScenarioResponse(BaseModel):
    scenario_id: str = Field(description="Unique scenario identifier, e.g., 'conflict_resolution_01'")
    target_dimension: SupportedDimension = Field(
        description="Core dimension influenced by this scenario"
    )
    perspective: Literal["self_behavior", "partner_expectation"] = Field(
        default="self_behavior",
        description="Distinguishes user's own action/behavior from what they expect in a partner"
    )
    normalized_preference: str = Field(
        description="Standardized categorical choice key, e.g., 'discuss_immediately', 'cool_down_first'"
    )
    expected_partner_preference: Optional[str] = Field(
        default=None,
        description="Optional explicitly stated preference for how partner should respond in this scenario"
    )
    raw_answer: Optional[str] = Field(
        default=None,
        description="Original verbatim answer text retained for natural language evidence tracing"
    )
    importance: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Relative importance weight of this scenario response"
    )

    @field_validator("importance")
    @classmethod
    def validate_finite_importance(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Scenario importance must be a finite floating point number.")
        return v

