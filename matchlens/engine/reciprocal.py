"""
Reciprocal score aggregation and evidence synthesis for MatchLens.
Combines directional scores S(A -> B) and S(B -> A) via geometric mean.
"""

import math
from typing import List
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import MatchResult, EvidenceSummary, DirectionalScore, EvidenceRecord
from matchlens.engine.eligibility import check_mutual_eligibility
from matchlens.engine.directional import calculate_directional_score
from matchlens.config import ALL_DIMENSIONS, DEFAULT_MIN_EVIDENCE_COVERAGE


def calculate_reciprocal_match(
    user_a: UserProfile,
    user_b: UserProfile,
    min_evidence_coverage: float = DEFAULT_MIN_EVIDENCE_COVERAGE,
) -> MatchResult:
    """
    Computes reciprocal compatibility score and produces structured evidence breakdown.

    Steps:
    1. Verify mutual eligibility. If not 'eligible', return MatchResult with status and reasons.
    2. Compute directional scores S(A -> B) and S(B -> A).
    3. Compute geometric mean: S_mutual = sqrt(S(A -> B) * S(B -> A)).
    4. Compute average evidence coverage score and flag low-coverage results.
    5. Synthesize structured EvidenceSummary for Gemini LLM explanation layer.
    """
    elig_status, inelig_reasons = check_mutual_eligibility(user_a, user_b)

    if elig_status != "eligible":
        return MatchResult(
            user_a_id=user_a.user_id,
            user_b_id=user_b.user_id,
            eligibility_status=elig_status,
            is_eligible=False,
            ineligibility_reasons=inelig_reasons,
            mutual_score=None,
            directional_a_to_b=None,
            directional_b_to_a=None,
            evidence_coverage=0.0,
            is_low_coverage=True,
            evidence_summary=None,
        )

    # Calculate directional compatibility scores
    dir_a_to_b = calculate_directional_score(user_a, user_b)
    dir_b_to_a = calculate_directional_score(user_b, user_a)

    score_a = dir_a_to_b.directional_score
    score_b = dir_b_to_a.directional_score

    # Compute reciprocal geometric mean score
    if score_a is not None and score_b is not None:
        mutual_score = math.sqrt(score_a * score_b)
        mutual_score = round(mutual_score, 2)
    else:
        mutual_score = None

    # Compute average evidence coverage
    avg_coverage = (dir_a_to_b.evidence_coverage + dir_b_to_a.evidence_coverage) / 2.0
    avg_coverage = round(avg_coverage, 2)
    is_low_coverage = avg_coverage < min_evidence_coverage

    # Synthesize evidence summary
    evidence_summary = _synthesize_evidence_summary(dir_a_to_b, dir_b_to_a)

    return MatchResult(
        user_a_id=user_a.user_id,
        user_b_id=user_b.user_id,
        eligibility_status="eligible",
        is_eligible=True,
        ineligibility_reasons=[],
        mutual_score=mutual_score,
        directional_a_to_b=dir_a_to_b,
        directional_b_to_a=dir_b_to_a,
        evidence_coverage=avg_coverage,
        is_low_coverage=is_low_coverage,
        evidence_summary=evidence_summary,
    )


def _synthesize_evidence_summary(
    dir_a_to_b: DirectionalScore, dir_b_to_a: DirectionalScore
) -> EvidenceSummary:
    """
    Synthesizes directional scores and evidence into a consolidated EvidenceSummary.
    """
    strengths: List[str] = []
    potential_differences: List[str] = []
    scenario_highlights: List[str] = []
    missing_data_warnings: List[str] = []
    structured_evidence: List[EvidenceRecord] = []

    # Aggregate shared strengths, differences, and structured records from both directions
    for dim_name in ALL_DIMENSIONS:
        dim_a = dir_a_to_b.dimension_scores.get(dim_name)
        dim_b = dir_b_to_a.dimension_scores.get(dim_name)

        if dim_a and dim_a.has_sufficient_data:
            strengths.extend(dim_a.shared_factors)
            potential_differences.extend(dim_a.gap_factors)
            scenario_highlights.extend(dim_a.scenario_evidence)
            structured_evidence.extend(dim_a.structured_records)
        else:
            missing_data_warnings.append(
                f"Dimension '{dim_name}' lacked sufficient profile data for evaluation by {dir_a_to_b.evaluator_id}."
            )

        if dim_b and dim_b.has_sufficient_data:
            strengths.extend(dim_b.shared_factors)
            potential_differences.extend(dim_b.gap_factors)
            scenario_highlights.extend(dim_b.scenario_evidence)
            structured_evidence.extend(dim_b.structured_records)
        else:
            missing_data_warnings.append(
                f"Dimension '{dim_name}' lacked sufficient profile data for evaluation by {dir_b_to_a.evaluator_id}."
            )

    # De-duplicate human-readable text lines
    strengths = list(dict.fromkeys(strengths))
    potential_differences = list(dict.fromkeys(potential_differences))
    scenario_highlights = list(dict.fromkeys(scenario_highlights))
    missing_data_warnings = list(dict.fromkeys(missing_data_warnings))

    return EvidenceSummary(
        strengths=strengths,
        potential_differences=potential_differences,
        scenario_highlights=scenario_highlights,
        missing_data_warnings=missing_data_warnings,
        structured_evidence=structured_evidence,
    )
