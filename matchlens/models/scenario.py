import math
from typing import Dict, List, Literal, Optional, Set
from pydantic import BaseModel, Field, field_validator, model_validator
from matchlens.config import SupportedDimension, DIMENSION_COMMUNICATION, DIMENSION_LIFESTYLE, DIMENSION_CORE_VALUES


class ScenarioDefinition(BaseModel):
    """
    Metadata definition for a known scenario in the system catalog.
    """
    scenario_id: str
    target_dimension: SupportedDimension
    title: str
    allowed_options: List[str]


# Pre-defined catalog of scenario assessments
KNOWN_SCENARIO_CATALOG: Dict[str, ScenarioDefinition] = {
    "conflict_resolution_01": ScenarioDefinition(
        scenario_id="conflict_resolution_01",
        target_dimension=DIMENSION_COMMUNICATION,
        title="Handling disagreement after a stressful day",
        allowed_options=["discuss_immediately", "cool_down_first", "written_first", "defer_to_partner"],
    ),
    "social_energy_01": ScenarioDefinition(
        scenario_id="social_energy_01",
        target_dimension=DIMENSION_LIFESTYLE,
        title="Weekend downtime preferences",
        allowed_options=["stay_home_quiet", "small_group_gathering", "large_party_outdoors", "spontaneous_travel"],
    ),
    "financial_planning_01": ScenarioDefinition(
        scenario_id="financial_planning_01",
        target_dimension=DIMENSION_CORE_VALUES,
        title="Approach to joint budgeting and major expenses",
        allowed_options=["strict_savings_first", "balanced_spending", "experience_focused", "independent_finances"],
    ),
}


class ScenarioCatalog:
    """
    Centralized catalog helper to validate scenario responses against known definitions.
    """
    @classmethod
    def get_definition(cls, scenario_id: str) -> Optional[ScenarioDefinition]:
        return KNOWN_SCENARIO_CATALOG.get(scenario_id)

    @classmethod
    def validate_response(cls, scenario_id: str, target_dimension: str, preference: str) -> List[str]:
        warnings = []
        defn = cls.get_definition(scenario_id)
        if defn:
            if defn.target_dimension != target_dimension:
                warnings.append(
                    f"Scenario '{scenario_id}' catalog target dimension is '{defn.target_dimension}', "
                    f"but response specifies '{target_dimension}'."
                )
            if preference and preference not in defn.allowed_options:
                warnings.append(
                    f"Option '{preference}' is not in catalog allowed options {defn.allowed_options} "
                    f"for scenario '{scenario_id}'."
                )
        return warnings


class ScenarioResponse(BaseModel):
    """
    Scenario-based assessment response.
    Captures self-reported behavior or partner expectations in a hypothetical situation.
    """
    scenario_id: str = Field(description="Unique scenario identifier, e.g., 'conflict_resolution_01'")
    target_dimension: SupportedDimension = Field(
        description="Core dimension influenced by this scenario"
    )
    perspective: Literal["self_behavior", "partner_expectation"] = Field(
        default="self_behavior",
        description="Explicitly indicates whether response describes user's own behavior or partner expectation"
    )
    normalized_preference: str = Field(
        description="Standardized categorical choice key describing user's self behavior or expectation"
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

    @model_validator(mode="after")
    def validate_against_catalog(self) -> "ScenarioResponse":
        # Check against scenario catalog if scenario_id is known
        defn = ScenarioCatalog.get_definition(self.scenario_id)
        if defn:
            if defn.target_dimension != self.target_dimension:
                raise ValueError(
                    f"Scenario '{self.scenario_id}' must have target_dimension '{defn.target_dimension}', got '{self.target_dimension}'."
                )
        return self
