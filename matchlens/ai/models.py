from typing import Generic, List, Literal, Optional, Set, TypeVar
from pydantic import BaseModel, Field, field_validator, model_validator
from matchlens.models.scenario import ScenarioResponse

T = TypeVar("T")

# Allowed categorical sets matching MatchLens profile models and scoring logic
ALLOWED_SMOKING = {"never", "socially", "regularly"}
ALLOWED_DRINKING = {"never", "socially", "regularly"}
ALLOWED_EXERCISE = {"daily", "weekly", "rarely", "never"}
ALLOWED_WANTS_CHILDREN = {"yes", "no", "open", "maybe"}
ALLOWED_RELATIONSHIP_INTENT = {"long_term", "marriage", "casual", "friendship"}
ALLOWED_COMMUNICATION_STYLE = {"direct", "gentle", "expressive", "analytical"}
ALLOWED_CONFLICT_RESOLUTION = {"discuss_immediately", "cool_down_first", "written_first"}
ALLOWED_CONTACT_FREQUENCY = {"frequent", "daily_check_in", "as_needed"}


def _normalize_category(val: Optional[str], allowed: Set[str], field_name: str) -> Optional[str]:
    """Helper to strip, lowercase, and validate categorical strings against allowed options."""
    if val is None:
        return None
    normalized = val.strip().lower()
    if normalized not in allowed:
        raise ValueError(
            f"Invalid value '{val}' for category '{field_name}'. Allowed options are: {sorted(list(allowed))}."
        )
    return normalized


def _normalize_category_list(vals: Optional[List[str]], allowed: Set[str], field_name: str) -> Optional[List[str]]:
    """Helper to strip, lowercase, and validate lists of categorical strings against allowed options."""
    if vals is None:
        return None
    normalized_list = []
    for item in vals:
        if item.strip().lower() in {"any", "all"}:
            normalized_list.append("any")
            continue
        norm = _normalize_category(item, allowed, field_name)
        if norm and norm not in normalized_list:
            normalized_list.append(norm)
    return normalized_list


class FieldExtraction(BaseModel, Generic[T]):
    """
    Wraps an extracted trait or preference with confidence scoring and evidence reasoning.
    """
    value: Optional[T] = Field(default=None, description="Extracted value or None if unstated/missing")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    reasoning: Optional[str] = Field(default=None, description="Reasoning or evidence text from user input")
    needs_confirmation: bool = Field(default=False, description="True if value is ambiguous or inferred with low certainty")


class PartialUserAttributes(BaseModel):
    """
    Partial user self-attributes explicitly confirmed by the user.
    Matches UserAttributes fields; missing/unstated values remain None.
    Categorical values are strictly normalized and validated.
    """
    age: Optional[int] = Field(default=None, ge=18, le=120)
    gender: Optional[str] = Field(default=None)
    relationship_intent: Optional[str] = Field(default=None)
    core_values: Optional[List[str]] = Field(default=None)
    interests: Optional[List[str]] = Field(default=None)
    smoking: Optional[str] = Field(default=None)
    drinking: Optional[str] = Field(default=None)
    exercise: Optional[str] = Field(default=None)
    has_children: Optional[bool] = Field(default=None)
    wants_children: Optional[str] = Field(default=None)
    communication_style: Optional[str] = Field(default=None)
    conflict_resolution: Optional[str] = Field(default=None)
    contact_frequency: Optional[str] = Field(default=None)

    @field_validator("smoking")
    @classmethod
    def validate_smoking(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_SMOKING, "smoking")

    @field_validator("drinking")
    @classmethod
    def validate_drinking(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_DRINKING, "drinking")

    @field_validator("exercise")
    @classmethod
    def validate_exercise(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_EXERCISE, "exercise")

    @field_validator("wants_children")
    @classmethod
    def validate_wants_children(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_WANTS_CHILDREN, "wants_children")

    @field_validator("relationship_intent")
    @classmethod
    def validate_relationship_intent(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_RELATIONSHIP_INTENT, "relationship_intent")

    @field_validator("communication_style")
    @classmethod
    def validate_communication_style(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_COMMUNICATION_STYLE, "communication_style")

    @field_validator("conflict_resolution")
    @classmethod
    def validate_conflict_resolution(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_CONFLICT_RESOLUTION, "conflict_resolution")

    @field_validator("contact_frequency")
    @classmethod
    def validate_contact_frequency(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v, ALLOWED_CONTACT_FREQUENCY, "contact_frequency")


class PartialPartnerPreferences(BaseModel):
    """
    Partial partner preferences explicitly confirmed by the user.
    Matches PartnerPreferences fields; missing/unstated values remain None.
    Categorical values are strictly normalized and validated.
    """
    min_age: Optional[int] = Field(default=None, ge=18)
    max_age: Optional[int] = Field(default=None, le=120)
    acceptable_genders: Optional[List[str]] = Field(default=None)
    desired_intentions: Optional[List[str]] = Field(default=None)
    desired_values: Optional[List[str]] = Field(default=None)
    acceptable_smoking: Optional[List[str]] = Field(default=None)
    acceptable_drinking: Optional[List[str]] = Field(default=None)
    desired_wants_children: Optional[List[str]] = Field(default=None)
    desired_communication_styles: Optional[List[str]] = Field(default=None)
    desired_conflict_resolutions: Optional[List[str]] = Field(default=None)

    @field_validator("acceptable_smoking")
    @classmethod
    def validate_acceptable_smoking(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_SMOKING, "acceptable_smoking")

    @field_validator("acceptable_drinking")
    @classmethod
    def validate_acceptable_drinking(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_DRINKING, "acceptable_drinking")

    @field_validator("desired_wants_children")
    @classmethod
    def validate_desired_wants_children(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_WANTS_CHILDREN, "desired_wants_children")

    @field_validator("desired_intentions")
    @classmethod
    def validate_desired_intentions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_RELATIONSHIP_INTENT, "desired_intentions")

    @field_validator("desired_communication_styles")
    @classmethod
    def validate_desired_communication_styles(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_COMMUNICATION_STYLE, "desired_communication_styles")

    @field_validator("desired_conflict_resolutions")
    @classmethod
    def validate_desired_conflict_resolutions(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        return _normalize_category_list(v, ALLOWED_CONFLICT_RESOLUTION, "desired_conflict_resolutions")


class PartialDealbreakers(BaseModel):
    """
    Partial dealbreakers explicitly stated by the user in natural language input.
    """
    strict_intention_match: Optional[bool] = Field(default=None)
    strict_age_range: Optional[bool] = Field(default=None)
    strict_gender_match: Optional[bool] = Field(default=None)
    smoking_dealbreaker: Optional[bool] = Field(default=None)
    children_dealbreaker: Optional[bool] = Field(default=None)
    blocked_user_ids: Optional[List[str]] = Field(default=None)


class ConfirmationPrompt(BaseModel):
    """
    Clarification prompt generated when user statements are ambiguous or inferred with lower confidence.
    These proposed inferences MUST NOT appear in confirmed attributes/preferences until confirmed by user.
    """
    field_name: str = Field(description="Target field requiring user confirmation")
    target_category: Literal["self_attributes", "partner_preferences", "dealbreakers"] = Field(
        description="Indicates whether this inference pertains to self attributes, partner preferences, or dealbreakers"
    )
    proposed_value: str = Field(description="AI's proposed normalized value inferred from user input")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence level of this proposed inference")
    reasoning: str = Field(description="Reasoning or excerpt explaining why this inference was made")
    clarification_question: str = Field(description="Targeted question asking user to confirm or correct the inference")


class ExtractedProfileUpdate(BaseModel):
    """
    Structured extraction contract returned by Groq AI integration layer.
    Explicitly separates confirmed user statements from unconfirmed inferences requiring user verification.
    """
    confirmed_self_attributes: PartialUserAttributes = Field(
        default_factory=PartialUserAttributes,
        description="Attributes explicitly and unambiguously stated by the user"
    )
    confirmed_partner_preferences: PartialPartnerPreferences = Field(
        default_factory=PartialPartnerPreferences,
        description="Partner preferences explicitly and unambiguously stated by the user"
    )
    confirmed_dealbreakers: PartialDealbreakers = Field(
        default_factory=PartialDealbreakers,
        description="Hard dealbreakers explicitly stated by the user"
    )
    scenarios: List[ScenarioResponse] = Field(
        default_factory=list,
        description="Validated scenario responses extracted from input"
    )
    unanswered_fields: List[str] = Field(
        default_factory=list,
        description="Relevant profile fields left unstated or unanswered by user"
    )
    uncertainties: List[str] = Field(
        default_factory=list,
        description="Ambiguous or vague user statements recorded for auditability"
    )
    confirmations_needed: List[ConfirmationPrompt] = Field(
        default_factory=list,
        description="Proposed inferences requiring explicit user confirmation before applying to profile"
    )

    @model_validator(mode="after")
    def validate_no_unconfirmed_inferences_in_confirmed_fields(self) -> "ExtractedProfileUpdate":
        """
        Enforces contract boundary: fields listed in confirmations_needed MUST NOT be present
        in confirmed_self_attributes, confirmed_partner_preferences, or confirmed_dealbreakers.
        """
        for prompt in self.confirmations_needed:
            field = prompt.field_name
            cat = prompt.target_category

            if cat == "self_attributes" and getattr(self.confirmed_self_attributes, field, None) is not None:
                raise ValueError(
                    f"Field '{field}' is marked as requiring confirmation in confirmations_needed, "
                    f"and therefore MUST NOT be set in confirmed_self_attributes."
                )
            elif cat == "partner_preferences" and getattr(self.confirmed_partner_preferences, field, None) is not None:
                raise ValueError(
                    f"Field '{field}' is marked as requiring confirmation in confirmations_needed, "
                    f"and therefore MUST NOT be set in confirmed_partner_preferences."
                )
            elif cat == "dealbreakers" and getattr(self.confirmed_dealbreakers, field, None) is not None:
                raise ValueError(
                    f"Field '{field}' is marked as requiring confirmation in confirmations_needed, "
                    f"and therefore MUST NOT be set in confirmed_dealbreakers."
                )
        return self
