from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field, field_validator
from matchlens.models.profile import UserAttributes, PartnerPreferences, Dealbreakers
from matchlens.models.scenario import ScenarioResponse

T = TypeVar("T")


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
    Partial user attributes extracted from natural language input.
    Matches UserAttributes fields; missing/unstated values remain None.
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


class PartialPartnerPreferences(BaseModel):
    """
    Partial partner preferences extracted from natural language input.
    Matches PartnerPreferences fields; missing/unstated values remain None.
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
    Clarification prompt generated when user statements are ambiguous or uncertain.
    """
    field_name: str = Field(description="Profile attribute or preference field name requiring confirmation")
    inferred_value: str = Field(description="Value inferred by AI from user statement")
    clarification_question: str = Field(description="Targeted question to ask the user to confirm or reject inference")


class ExtractedProfileUpdate(BaseModel):
    """
    Structured extraction contract returned by Groq AI integration layer.
    Explicitly distinguishes self attributes, partner expectations, dealbreakers,
    unanswered/uncertain info, and items needing user confirmation.
    """
    self_attributes: PartialUserAttributes = Field(default_factory=PartialUserAttributes)
    partner_preferences: PartialPartnerPreferences = Field(default_factory=PartialPartnerPreferences)
    dealbreakers: PartialDealbreakers = Field(default_factory=PartialDealbreakers)
    scenarios: List[ScenarioResponse] = Field(default_factory=list)
    unanswered_fields: List[str] = Field(default_factory=list, description="Fields relevant to current context that user did not answer")
    uncertainties: List[str] = Field(default_factory=list, description="Ambiguous statements in user input")
    confirmations_needed: List[ConfirmationPrompt] = Field(default_factory=list, description="Items where AI made an assumption needing confirmation")
