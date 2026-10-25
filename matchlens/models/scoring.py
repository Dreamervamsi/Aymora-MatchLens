from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

EligibilityStatus = Literal["eligible", "ineligible", "pending_information"]


class EvidenceRecord(BaseModel):
    """
    Structured evidence record tracing source data to scoring outcomes.
    """
    dimension_name: str
    source_type: Literal["attribute", "scenario"]
    source_id: str = Field(description="Attribute name or scenario ID")
    evaluator_expectation: Any = Field(default=None, description="Evaluator's requested value or expectation")
    candidate_value: Any = Field(default=None, description="Candidate's self-reported attribute or scenario behavior")
    outcome: Literal["match", "partial", "mismatch", "missing"]
    score_impact: Optional[float] = Field(default=None, description="Sub-score contribution [0.0 - 100.0]")
    is_scoring_factor: bool = Field(default=True, description="True if this evidence influenced the dimension score")


class DimensionScore(BaseModel):
    dimension_name: str
    score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Normalized compatibility score [0-100], or None if data is insufficient"
    )
    weight: float = Field(description="Applied user weight for this dimension")
    weighted_contribution: Optional[float] = Field(
        default=None,
        description="Score * weight / sum_active_weights"
    )
    has_sufficient_data: bool = Field(default=True)
    structured_records: List[EvidenceRecord] = Field(
        default_factory=list,
        description="Structured, fully-traceable evidence records"
    )
    shared_factors: List[str] = Field(default_factory=list, description="Derived human-readable alignment points")
    gap_factors: List[str] = Field(default_factory=list, description="Derived human-readable gap factors")
    scenario_evidence: List[str] = Field(default_factory=list, description="Derived human-readable scenario evidence lines")


class DirectionalScore(BaseModel):
    evaluator_id: str
    candidate_id: str
    directional_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Overall weighted directional compatibility score [0-100]"
    )
    total_active_weight: float = Field(description="Sum of weights for dimensions with sufficient data")
    evidence_coverage: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of total intended assessment supported by data"
    )
    dimension_scores: Dict[str, DimensionScore] = Field(default_factory=dict)


class EvidenceSummary(BaseModel):
    strengths: List[str] = Field(default_factory=list, description="Key shared strengths / alignment points")
    potential_differences: List[str] = Field(default_factory=list, description="Areas of divergence or caution")
    scenario_highlights: List[str] = Field(default_factory=list, description="Scenario-backed evidence lines")
    missing_data_warnings: List[str] = Field(default_factory=list, description="Dimensions lacking profile evidence")
    structured_evidence: List[EvidenceRecord] = Field(default_factory=list, description="Consolidated structured evidence records")


class MatchResult(BaseModel):
    user_a_id: str
    user_b_id: str
    eligibility_status: EligibilityStatus = Field(
        default="eligible",
        description="Eligibility state: 'eligible', 'ineligible', or 'pending_information'"
    )
    is_eligible: bool = Field(
        default=True,
        description="True only if eligibility_status == 'eligible'"
    )
    ineligibility_reasons: List[str] = Field(default_factory=list, description="Reasons for exclusion or pending information")
    mutual_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Geometric mean of both directional scores: sqrt(S(A->B) * S(B->A))"
    )
    directional_a_to_b: Optional[DirectionalScore] = None
    directional_b_to_a: Optional[DirectionalScore] = None
    evidence_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Average evidence coverage between both directional evaluations"
    )
    is_low_coverage: bool = Field(
        default=False,
        description="True if evidence coverage is below minimum threshold (e.g. 60%)"
    )
    evidence_summary: Optional[EvidenceSummary] = None
