import math
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field, model_validator, field_validator
from matchlens.config import DEFAULT_DIMENSION_WEIGHTS, ALL_DIMENSIONS
from matchlens.models.scenario import ScenarioResponse


class DimensionWeights(BaseModel):
    core_values: float = Field(default=DEFAULT_DIMENSION_WEIGHTS["core_values"], ge=0.0)
    relationship_intentions: float = Field(default=DEFAULT_DIMENSION_WEIGHTS["relationship_intentions"], ge=0.0)
    lifestyle_compatibility: float = Field(default=DEFAULT_DIMENSION_WEIGHTS["lifestyle_compatibility"], ge=0.0)
    communication_preferences: float = Field(default=DEFAULT_DIMENSION_WEIGHTS["communication_preferences"], ge=0.0)
    shared_interests: float = Field(default=DEFAULT_DIMENSION_WEIGHTS["shared_interests"], ge=0.0)

    @field_validator("core_values", "relationship_intentions", "lifestyle_compatibility", "communication_preferences", "shared_interests")
    @classmethod
    def validate_finite_weight(cls, v: float) -> float:
        if not math.isfinite(v):
            raise ValueError("Dimension weights must be finite numbers.")
        return v

    @model_validator(mode="after")
    def validate_weights_total(self) -> "DimensionWeights":
        total = (
            self.core_values
            + self.relationship_intentions
            + self.lifestyle_compatibility
            + self.communication_preferences
            + self.shared_interests
        )
        if total <= 0:
            raise ValueError("Total applicable user weights must be greater than 0.")
        return self

    def get_dict(self) -> Dict[str, float]:
        return {
            "core_values": self.core_values,
            "relationship_intentions": self.relationship_intentions,
            "lifestyle_compatibility": self.lifestyle_compatibility,
            "communication_preferences": self.communication_preferences,
            "shared_interests": self.shared_interests,
        }


class UserAttributes(BaseModel):
    """
    A user's own self-reported characteristics.
    """
    age: Optional[int] = Field(default=None, ge=18, le=120)
    gender: Optional[str] = Field(default=None, description="e.g. 'man', 'woman', 'non-binary'")
    relationship_intent: Optional[str] = Field(
        default=None,
        description="e.g. 'long_term', 'marriage', 'casual', 'friendship'"
    )
    core_values: Optional[List[str]] = Field(default=None, description="e.g. ['honesty', 'family', 'ambition']. None indicates missing/unanswered.")
    interests: Optional[List[str]] = Field(default=None, description="e.g. ['hiking', 'reading', 'cooking']. None indicates missing/unanswered.")
    
    # Lifestyle attributes
    smoking: Optional[str] = Field(default=None, description="'never', 'socially', 'regularly'")
    drinking: Optional[str] = Field(default=None, description="'never', 'socially', 'regularly'")
    exercise: Optional[str] = Field(default=None, description="'daily', 'weekly', 'rarely', 'never'")
    has_children: Optional[bool] = Field(default=None)
    wants_children: Optional[str] = Field(default=None, description="'yes', 'no', 'open', 'maybe'")
    
    # Communication style attributes
    communication_style: Optional[str] = Field(default=None, description="'direct', 'gentle', 'expressive', 'analytical'")
    conflict_resolution: Optional[str] = Field(default=None, description="'discuss_immediately', 'cool_down_first', 'written_first'")
    contact_frequency: Optional[str] = Field(default=None, description="'frequent', 'daily_check_in', 'as_needed'")


class PartnerPreferences(BaseModel):
    """
    User's expectations and desired traits in a prospective partner.
    Semantics for missing vs unrestricted preferences:
    - None: Missing/unanswered data (affects coverage score).
    - [] or ['any']: Unrestricted / Open to all options.
    """
    min_age: Optional[int] = Field(default=18, ge=18)
    max_age: Optional[int] = Field(default=120, le=120)
    acceptable_genders: Optional[List[str]] = Field(
        default_factory=list,
        description="Genders user is open to dating. Empty [] or ['any'] means open to any gender."
    )
    desired_intentions: Optional[List[str]] = Field(
        default=None,
        description="Acceptable relationship intentions in partner. None means unstated."
    )
    desired_values: Optional[List[str]] = Field(
        default=None,
        description="Core values expected in a partner. None means unstated."
    )
    acceptable_smoking: Optional[List[str]] = Field(
        default=None,
        description="e.g. ['never', 'socially']. None means unstated."
    )
    acceptable_drinking: Optional[List[str]] = Field(
        default=None,
        description="e.g. ['never', 'socially']. None means unstated."
    )
    desired_wants_children: Optional[List[str]] = Field(
        default=None,
        description="Acceptable positions on children. None means unstated."
    )
    desired_communication_styles: Optional[List[str]] = Field(
        default=None,
        description="Preferred communication styles in a partner. None means unstated."
    )
    desired_conflict_resolutions: Optional[List[str]] = Field(
        default=None,
        description="Preferred conflict resolution styles in a partner. None means unstated."
    )

    @model_validator(mode="after")
    def validate_age_range(self) -> "PartnerPreferences":
        if self.min_age is not None and self.max_age is not None:
            if self.min_age > self.max_age:
                raise ValueError(f"Minimum age preference ({self.min_age}) cannot exceed maximum age ({self.max_age}).")
        return self


class Dealbreakers(BaseModel):
    """
    Hard mandatory restrictions that fail eligibility if violated.
    """
    strict_intention_match: bool = Field(default=True, description="Must have compatible relationship intentions")
    strict_age_range: bool = Field(default=True, description="Must be within age limits")
    strict_gender_match: bool = Field(default=True, description="Must match target gender preferences")
    smoking_dealbreaker: bool = Field(default=False, description="Strictly forbid smoking if non-acceptable")
    children_dealbreaker: bool = Field(default=False, description="Strictly forbid disagreement on children")
    blocked_user_ids: List[str] = Field(default_factory=list, description="Explicitly blocked user IDs")


class UserProfile(BaseModel):
    """
    Complete structured user profile.
    Distinguishes self characteristics from partner expectations.
    """
    user_id: str = Field(description="Unique identifier for the user")
    attributes: UserAttributes = Field(default_factory=UserAttributes)
    expectations: PartnerPreferences = Field(default_factory=PartnerPreferences)
    dealbreakers: Dealbreakers = Field(default_factory=Dealbreakers)
    weights: DimensionWeights = Field(default_factory=DimensionWeights)
    scenarios: List[ScenarioResponse] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_scenario_ids(self) -> "UserProfile":
        seen_ids = set()
        for scenario in self.scenarios:
            if scenario.scenario_id in seen_ids:
                raise ValueError(f"Duplicate scenario_id found in profile: '{scenario.scenario_id}'")
            seen_ids.add(scenario.scenario_id)
        return self

