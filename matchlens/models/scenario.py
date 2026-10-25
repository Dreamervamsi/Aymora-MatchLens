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
    description: Optional[str] = None
    self_prompt: Optional[str] = None
    partner_prompt: Optional[str] = None
    option_descriptions: Optional[Dict[str, str]] = None


# Pre-defined catalog of scenario assessments
KNOWN_SCENARIO_CATALOG: Dict[str, ScenarioDefinition] = {
    "conflict_resolution_01": ScenarioDefinition(
        scenario_id="conflict_resolution_01",
        target_dimension=DIMENSION_COMMUNICATION,
        title="Handling disagreement after a stressful day",
        allowed_options=["discuss_immediately", "cool_down_first", "written_first", "defer_to_partner"],
        description="A major disagreement arises at the end of a long, stressful workday.",
        self_prompt="What would you most likely do in this situation?",
        partner_prompt="What would you prefer or be comfortable with your partner doing in the same situation?",
        option_descriptions={
            "discuss_immediately": "Talk through the issue immediately to clear the air.",
            "cool_down_first": "Take time alone to process before discussing.",
            "written_first": "Express thoughts in a text or letter before talking.",
            "defer_to_partner": "Let partner take the lead on when and how to resolve.",
        },
    ),
    "social_energy_01": ScenarioDefinition(
        scenario_id="social_energy_01",
        target_dimension=DIMENSION_LIFESTYLE,
        title="Weekend downtime preferences",
        allowed_options=["stay_home_quiet", "small_group_gathering", "large_party_outdoors", "spontaneous_travel"],
        description="You have a completely free weekend after a demanding week.",
        self_prompt="What would you most likely do in this situation?",
        partner_prompt="What would you prefer or be comfortable with your partner doing in the same situation?",
        option_descriptions={
            "stay_home_quiet": "Relax quietly at home with minimal social interaction.",
            "small_group_gathering": "Host or attend a quiet gathering with a few close friends.",
            "large_party_outdoors": "Attend a large social event, party, or outdoor festival.",
            "spontaneous_travel": "Go on an unplanned weekend getaway or trip.",
        },
    ),
    "financial_planning_01": ScenarioDefinition(
        scenario_id="financial_planning_01",
        target_dimension=DIMENSION_CORE_VALUES,
        title="Approach to joint budgeting and major expenses",
        allowed_options=["strict_savings_first", "balanced_spending", "experience_focused", "independent_finances"],
        description="You are deciding how to manage money and allocate savings for future goals.",
        self_prompt="What would you most likely do in this situation?",
        partner_prompt="What would you prefer or be comfortable with your partner doing in the same situation?",
        option_descriptions={
            "strict_savings_first": "Prioritize strict savings and emergency reserves above all.",
            "balanced_spending": "Maintain a balanced approach between saving and moderate spending.",
            "experience_focused": "Prioritize spending on experiences, travel, and current enjoyment.",
            "independent_finances": "Keep finances mostly separate with shared responsibilities.",
        },
    ),
}


class ScenarioCatalog:
    """
    Centralized catalog helper to validate scenario responses against known definitions.
    """
    DEFAULT_SCENARIOS: List[str] = [
        "conflict_resolution_01",
        "social_energy_01",
        "financial_planning_01",
    ]

    @classmethod
    def get_definition(cls, scenario_id: str) -> Optional[ScenarioDefinition]:
        return KNOWN_SCENARIO_CATALOG.get(scenario_id)

    @classmethod
    def list_scenarios(cls) -> List[ScenarioDefinition]:
        return list(KNOWN_SCENARIO_CATALOG.values())


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
        defn = ScenarioCatalog.get_definition(self.scenario_id)
        if defn:
            if defn.target_dimension != self.target_dimension:
                raise ValueError(
                    f"Scenario '{self.scenario_id}' catalog target_dimension is '{defn.target_dimension}', "
                    f"got '{self.target_dimension}'."
                )
            norm_pref = self.normalized_preference.strip().lower() if self.normalized_preference else ""
            if norm_pref not in defn.allowed_options:
                raise ValueError(
                    f"Option '{self.normalized_preference}' is not an allowed option {defn.allowed_options} "
                    f"for scenario '{self.scenario_id}'."
                )
            if self.expected_partner_preference:
                exp_pref = self.expected_partner_preference.strip().lower()
                if exp_pref not in defn.allowed_options:
                    raise ValueError(
                        f"Expected partner option '{self.expected_partner_preference}' is not an allowed option {defn.allowed_options} "
                        f"for scenario '{self.scenario_id}'."
                    )
        return self
