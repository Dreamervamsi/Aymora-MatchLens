"""
Directional weighted compatibility scoring and missing data handling for MatchLens.
Calculates S(Evaluator -> Candidate) using evaluator's weights and active dimension scores.
Ensures single-pass scorer execution per comparison.
"""

from typing import Dict, Tuple, List
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import DirectionalScore, DimensionScore, EvidenceRecord
from matchlens.engine.dimension_scorers import (
    score_core_values,
    score_relationship_intentions,
    score_lifestyle,
    score_communication,
    score_shared_interests,
)
from matchlens.config import (
    DIMENSION_CORE_VALUES,
    DIMENSION_RELATIONSHIP_INTENTIONS,
    DIMENSION_LIFESTYLE,
    DIMENSION_COMMUNICATION,
    DIMENSION_INTERESTS,
    ALL_DIMENSIONS,
)


def calculate_directional_score(evaluator: UserProfile, candidate: UserProfile) -> DirectionalScore:
    """
    Computes S(Evaluator -> Candidate) directional compatibility score.

    Single-pass execution: calls each dimension scorer function exactly once.

    Formula:
      S(A -> B) = sum(w_{A,i} * s_i(A,B)) / sum(w_{A,i} for active i)

    Missing Data Handling:
    - Dimensions where score is None (insufficient data) are marked with has_sufficient_data = False.
    - Missing dimensions are excluded from sum of active weights.
    - evidence_coverage = (sum of active weights / sum of all dimension weights) * 100%.
    """
    weights_dict = evaluator.weights.get_dict()
    total_intended_weight = sum(weights_dict.values())

    scorers = {
        DIMENSION_CORE_VALUES: score_core_values,
        DIMENSION_RELATIONSHIP_INTENTIONS: score_relationship_intentions,
        DIMENSION_LIFESTYLE: score_lifestyle,
        DIMENSION_COMMUNICATION: score_communication,
        DIMENSION_INTERESTS: score_shared_interests,
    }

    # Execute each dimension scorer exactly once
    raw_results = {}
    total_active_weight = 0.0

    for dim_name in ALL_DIMENSIONS:
        scorer_fn = scorers[dim_name]
        score_val, shared, gaps, scenario_ev, records = scorer_fn(evaluator, candidate)
        w = weights_dict.get(dim_name, 0.0)

        has_data = score_val is not None
        if has_data:
            total_active_weight += w

        raw_results[dim_name] = {
            "score_val": score_val,
            "weight": w,
            "has_data": has_data,
            "shared": shared,
            "gaps": gaps,
            "scenario_ev": scenario_ev,
            "records": records,
        }

    # Construct DimensionScore objects and calculate overall directional score
    dimension_scores: Dict[str, DimensionScore] = {}
    weighted_score_sum = 0.0

    for dim_name in ALL_DIMENSIONS:
        res = raw_results[dim_name]
        score_val = res["score_val"]
        w = res["weight"]
        has_data = res["has_data"]

        if has_data and total_active_weight > 0.0:
            weighted_contrib = (score_val * w) / total_active_weight
            weighted_score_sum += score_val * w
        else:
            weighted_contrib = None

        dimension_scores[dim_name] = DimensionScore(
            dimension_name=dim_name,
            score=score_val,
            weight=w,
            weighted_contribution=round(weighted_contrib, 2) if weighted_contrib is not None else None,
            has_sufficient_data=has_data,
            structured_records=res["records"],
            shared_factors=res["shared"],
            gap_factors=res["gaps"],
            scenario_evidence=res["scenario_ev"],
        )

    if total_active_weight > 0.0:
        overall_directional_score = weighted_score_sum / total_active_weight
        overall_directional_score = round(overall_directional_score, 2)
    else:
        overall_directional_score = None

    if total_intended_weight > 0.0:
        evidence_coverage = (total_active_weight / total_intended_weight) * 100.0
        evidence_coverage = round(evidence_coverage, 2)
    else:
        evidence_coverage = 0.0

    return DirectionalScore(
        evaluator_id=evaluator.user_id,
        candidate_id=candidate.user_id,
        directional_score=overall_directional_score,
        total_active_weight=round(total_active_weight, 4),
        evidence_coverage=evidence_coverage,
        dimension_scores=dimension_scores,
    )
