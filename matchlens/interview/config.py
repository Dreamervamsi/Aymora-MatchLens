from typing import List
from pydantic import BaseModel, Field


class InterviewSettings(BaseModel):
    """
    Configuration settings for conversational interview orchestration.
    """
    max_total_turns: int = Field(
        default=20,
        ge=1,
        description="Maximum turns before forcing readiness review"
    )
    max_turns_per_topic: int = Field(
        default=3,
        ge=1,
        description="Maximum turns allocated per interview topic before advancing"
    )
    essential_self_fields: List[str] = Field(
        default_factory=lambda: [
            "age",
            "gender",
            "relationship_intent",
        ],
        description="Core self-attribute fields required for profile completeness"
    )
    essential_partner_fields: List[str] = Field(
        default_factory=lambda: [
            "acceptable_genders",
        ],
        description="Core partner preference fields required for profile completeness"
    )
    allow_early_finish: bool = Field(
        default=True,
        description="Whether to allow user to trigger early completion review"
    )
