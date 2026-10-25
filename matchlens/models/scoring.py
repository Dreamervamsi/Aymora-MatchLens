from typing import Dict, List, Optional
from pydantic import BaseModel, Field

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
    shared_factors: List[str] = Field(default_factory=list, description="Positive alignment factors / evidence")
    gap_factors: List[str] = Field(default_factory=list, description="Gaps, differences, or mismatches")
    scenario_evidence: List[str] = Field(default_factory=list, description="Supporting evidence from scenarios")


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


from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

EligibilityStatus = Literal["eligible", "ineligible", "pending_information"]

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
    shared_factors: List[str] = Field(default_factory=list, description="Positive alignment factors / evidence")
    gap_factors: List[str] = Field(default_factory=list, description="Gaps, differences, or mismatches")
    scenario_evidence: List[str] = Field(default_factory=list, description="Supporting evidence from scenarios")


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
    evidence_summary: Optional[EvidenceSummary] = None
