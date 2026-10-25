from typing import Dict, Tuple
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import DirectionalScore, DimensionScore
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

    Formula:
      S(A -> B) = sum(w_{A,i} * s_i(A,B)) / sum(w_{A,i} for active i)

    Missing Data Handling:
    - Dimensions where score is None (insufficient data) are marked with has_sufficient_data = False.
    - Missing dimensions are excluded from sum of active weights.
    - evidence_coverage = (sum of active weights / sum of all dimension weights) * 100%.
    """
    weights_dict = evaluator.weights.get_dict()
    total_intended_weight = sum(weights_dict.values())

    # Map dimensions to their scoring function
    scorers = {
        DIMENSION_CORE_VALUES: score_core_values,
        DIMENSION_RELATIONSHIP_INTENTIONS: score_relationship_intentions,
        DIMENSION_LIFESTYLE: score_lifestyle,
        DIMENSION_COMMUNICATION: score_communication,
        DIMENSION_INTERESTS: score_shared_interests,
    }

    dimension_scores: Dict[str, DimensionScore] = {}
    total_active_weight = 0.0
    weighted_score_sum = 0.0

    # 1. First pass: score each dimension and sum active weights
    for dim_name in ALL_DIMENSIONS:
        scorer_fn = scorers[dim_name]
        score_val, shared_factors, gap_factors, scenario_evidence = scorer_fn(evaluator, candidate)
        w = weights_dict.get(dim_name, 0.0)

        if score_val is not None:
            total_active_weight += w

    # 2. Second pass: compute weighted contribution relative to sum of active weights
    for dim_name in ALL_DIMENSIONS:
        scorer_fn = scorers[dim_name]
        score_val, shared_factors, gap_factors, scenario_evidence = scorer_fn(evaluator, candidate)
        w = weights_dict.get(dim_name, 0.0)

        if score_val is not None and total_active_weight > 0.0:
            weighted_contrib = (score_val * w) / total_active_weight
            weighted_score_sum += score_val * w
            has_data = True
        else:
            weighted_contrib = None
            has_data = False

        dimension_scores[dim_name] = DimensionScore(
            dimension_name=dim_name,
            score=score_val,
            weight=w,
            weighted_contribution=round(weighted_contrib, 2) if weighted_contrib is not None else None,
            has_sufficient_data=has_data,
            shared_factors=shared_factors,
            gap_factors=gap_factors,
            scenario_evidence=scenario_evidence,
        )

    # Calculate overall directional score and evidence coverage
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
