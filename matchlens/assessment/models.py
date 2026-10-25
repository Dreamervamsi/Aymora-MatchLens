from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from matchlens.models.scenario import ScenarioResponse, ScenarioCatalog, ScenarioDefinition


class AssessmentStatus(str, Enum):
    ACTIVE = "active"
    READY_FOR_REVIEW = "ready_for_review"
    COMPLETED = "completed"


class AssessmentStage(str, Enum):
    SELF_BEHAVIOR = "self_behavior"
    PARTNER_EXPECTATION = "partner_expectation"
    REVIEW = "review"
    COMPLETED = "completed"


class ClarificationRequest(BaseModel):
    """
    Captures an ambiguous AI interpretation requiring user clarification.
    """
    scenario_id: str
    stage: AssessmentStage
    raw_input: str
    proposed_option: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning: str
    clarification_prompt: str


class ScenarioDraftResponse(BaseModel):
    """
    Intermediate response data collected for a single scenario.
    """
    scenario_id: str
    target_dimension: str
    self_response: Optional[str] = None
    self_raw_input: Optional[str] = None
    partner_expectation: Optional[str] = None
    partner_raw_input: Optional[str] = None
    importance: float = Field(default=1.0, ge=0.0, le=2.0)

    @model_validator(mode="after")
    def validate_options(self) -> "ScenarioDraftResponse":
        defn = ScenarioCatalog.get_definition(self.scenario_id)
        if defn:
            if self.self_response and self.self_response.strip().lower() not in defn.allowed_options:
                raise ValueError(f"Self response '{self.self_response}' is invalid for scenario '{self.scenario_id}'.")
            if self.partner_expectation and self.partner_expectation.strip().lower() not in defn.allowed_options:
                raise ValueError(f"Partner expectation '{self.partner_expectation}' is invalid for scenario '{self.scenario_id}'.")
        return self

    def is_complete(self) -> bool:
        return self.self_response is not None and self.partner_expectation is not None


class AssessmentProgress(BaseModel):
    current_scenario_index: int = 0
    total_scenarios: int = 0
    completed_scenario_ids: List[str] = Field(default_factory=list)
    current_stage: AssessmentStage = AssessmentStage.SELF_BEHAVIOR
    percentage: float = Field(default=0.0, ge=0.0, le=100.0)


class AssessmentState(BaseModel):
    """
    Serializable state for a scenario-based relationship assessment session.
    """
    assessment_id: str
    user_id: str
    selected_scenario_ids: List[str] = Field(default_factory=list)
    current_scenario_index: int = 0
    current_stage: AssessmentStage = AssessmentStage.SELF_BEHAVIOR
    collected_responses: Dict[str, ScenarioDraftResponse] = Field(default_factory=dict)
    unresolved_clarification: Optional[ClarificationRequest] = None
    status: AssessmentStatus = AssessmentStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    progress: AssessmentProgress = Field(default_factory=AssessmentProgress)

    @model_validator(mode="after")
    def validate_scenarios_exist(self) -> "AssessmentState":
        for sid in self.selected_scenario_ids:
            if not ScenarioCatalog.get_definition(sid):
                raise ValueError(f"Unknown scenario ID '{sid}' in selected scenarios.")
        return self


class AssessmentTurnResult(BaseModel):
    """
    Atomic output returned to caller after each assessment turn.
    """
    assessment_id: str
    status: AssessmentStatus
    current_stage: AssessmentStage
    current_scenario_id: Optional[str] = None
    scenario_definition: Optional[ScenarioDefinition] = None
    prompt_text: str
    allowed_options: List[str] = Field(default_factory=list)
    unresolved_clarification: Optional[ClarificationRequest] = None
    progress: AssessmentProgress
    summary_data: Optional[Dict[str, Any]] = None
