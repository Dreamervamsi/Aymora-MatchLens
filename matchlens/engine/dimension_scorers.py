"""
Pure deterministic dimension scoring and scenario alignment functions for MatchLens.
Calculates score [0.0 - 100.0], shared factors, gap factors, and scenario evidence.
"""

from typing import List, Optional, Tuple, Set, Dict
from matchlens.models.profile import UserProfile
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.eligibility import normalize_str, normalize_str_list
from matchlens.config import (
    DIMENSION_CORE_VALUES,
    DIMENSION_RELATIONSHIP_INTENTIONS,
    DIMENSION_LIFESTYLE,
    DIMENSION_COMMUNICATION,
    DIMENSION_INTERESTS,
)


def score_core_values(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates core values compatibility.
    Evaluator desired_values vs Candidate core_values.
    """
    desired = normalize_str_list(evaluator.expectations.desired_values)
    cand_values = normalize_str_list(candidate.attributes.core_values)

    attr_score = None
    shared_factors = []
    gap_factors = []

    if desired and cand_values:
        desired_set = set(desired)
        cand_set = set(cand_values)

        matched = desired_set.intersection(cand_set)
        missing = desired_set.difference(cand_set)

        attr_score = (len(matched) / len(desired_set)) * 100.0

        shared_factors = [f"[core_values] Shared core value: '{m}'" for m in sorted(matched)]
        gap_factors = [f"[core_values] Desired value '{m}' missing in candidate profile" for m in sorted(missing)]

    scenario_score, scenario_evidence = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_CORE_VALUES
    )

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared_factors, gap_factors, scenario_evidence


def score_relationship_intentions(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates relationship intentions compatibility.
    Candidate relationship_intent vs Evaluator desired_intentions.
    """
    desired_intentions = normalize_str_list(evaluator.expectations.desired_intentions)
    cand_intent = normalize_str(candidate.attributes.relationship_intent)

    attr_score = None
    shared = []
    gaps = []

    if desired_intentions and cand_intent:
        if cand_intent in desired_intentions:
            attr_score = 100.0
            shared = [f"[relationship_intentions] Candidate's intent '{candidate.attributes.relationship_intent}' matches evaluator's expectations"]
        else:
            attr_score = 0.0
            gaps = [f"[relationship_intentions] Candidate's intent '{candidate.attributes.relationship_intent}' differs from evaluator's expectations {evaluator.expectations.desired_intentions}"]

    scenario_score, scenario_evidence = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_RELATIONSHIP_INTENTIONS
    )

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared, gaps, scenario_evidence


def score_lifestyle(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates lifestyle compatibility across sub-attributes and scenarios.
    """
    exp = evaluator.expectations
    c_attr = candidate.attributes

    sub_scores = []
    shared_factors = []
    gap_factors = []

    # 1. Smoking
    norm_acc_smoking = normalize_str_list(exp.acceptable_smoking)
    norm_c_smoking = normalize_str(c_attr.smoking)
    if norm_acc_smoking and norm_c_smoking:
        if norm_c_smoking in norm_acc_smoking:
            sub_scores.append(100.0)
            shared_factors.append(f"[lifestyle_compatibility] Acceptable smoking habit: '{c_attr.smoking}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"[lifestyle_compatibility] Smoking habit '{c_attr.smoking}' not in acceptable options {exp.acceptable_smoking}")

    # 2. Drinking
    norm_acc_drinking = normalize_str_list(exp.acceptable_drinking)
    norm_c_drinking = normalize_str(c_attr.drinking)
    if norm_acc_drinking and norm_c_drinking:
        if norm_c_drinking in norm_acc_drinking:
            sub_scores.append(100.0)
            shared_factors.append(f"[lifestyle_compatibility] Acceptable drinking habit: '{c_attr.drinking}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"[lifestyle_compatibility] Drinking habit '{c_attr.drinking}' not in acceptable options {exp.acceptable_drinking}")

    # 3. Children stance
    norm_acc_children = normalize_str_list(exp.desired_wants_children)
    norm_c_children = normalize_str(c_attr.wants_children)
    if norm_acc_children and norm_c_children:
        if norm_c_children in norm_acc_children:
            sub_scores.append(100.0)
            shared_factors.append(f"[lifestyle_compatibility] Aligned position on children: '{c_attr.wants_children}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"[lifestyle_compatibility] Stance on children '{c_attr.wants_children}' not in preferred options {exp.desired_wants_children}")

    attr_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    scenario_score, scenario_evidence = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_LIFESTYLE
    )

    final_score = _blend_dimension_scores(attr_score, scenario_score, attr_weight=0.6, scenario_weight=0.4)
    return final_score, shared_factors, gap_factors, scenario_evidence


def score_communication(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates communication preferences & conflict resolution.
    """
    exp = evaluator.expectations
    c_attr = candidate.attributes

    sub_scores = []
    shared_factors = []
    gap_factors = []

    # 1. Communication style
    norm_desired_styles = normalize_str_list(exp.desired_communication_styles)
    norm_c_style = normalize_str(c_attr.communication_style)
    if norm_desired_styles and norm_c_style:
        if norm_c_style in norm_desired_styles:
            sub_scores.append(100.0)
            shared_factors.append(f"[communication_preferences] Preferred communication style: '{c_attr.communication_style}'")
        else:
            sub_scores.append(25.0)
            gap_factors.append(f"[communication_preferences] Communication style '{c_attr.communication_style}' differs from preferred styles {exp.desired_communication_styles}")

    # 2. Conflict resolution
    norm_desired_conflicts = normalize_str_list(exp.desired_conflict_resolutions)
    norm_c_conflict = normalize_str(c_attr.conflict_resolution)
    if norm_desired_conflicts and norm_c_conflict:
        if norm_c_conflict in norm_desired_conflicts:
            sub_scores.append(100.0)
            shared_factors.append(f"[communication_preferences] Aligned conflict resolution style: '{c_attr.conflict_resolution}'")
        else:
            sub_scores.append(25.0)
            gap_factors.append(f"[communication_preferences] Conflict resolution style '{c_attr.conflict_resolution}' differs from preferred styles {exp.desired_conflict_resolutions}")

    attr_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    scenario_score, scenario_evidence = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_COMMUNICATION
    )

    final_score = _blend_dimension_scores(attr_score, scenario_score, attr_weight=0.5, scenario_weight=0.5)
    return final_score, shared_factors, gap_factors, scenario_evidence


def score_shared_interests(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates shared interests using Jaccard similarity.
    """
    eval_interests = normalize_str_list(evaluator.attributes.interests)
    cand_interests = normalize_str_list(candidate.attributes.interests)

    attr_score = None
    shared_factors = []
    gap_factors = []

    if eval_interests and cand_interests:
        e_set = set(eval_interests)
        c_set = set(cand_interests)

        intersection = e_set.intersection(c_set)
        union = e_set.union(c_set)

        if union:
            attr_score = (len(intersection) / len(union)) * 100.0
            shared_factors = [f"[shared_interests] Shared interest: '{i}'" for i in sorted(intersection)]

    scenario_score, scenario_evidence = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_INTERESTS
    )

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared_factors, gap_factors, scenario_evidence


def _blend_dimension_scores(
    attr_score: Optional[float],
    scenario_score: Optional[float],
    attr_weight: float = 0.5,
    scenario_weight: float = 0.5,
) -> Optional[float]:
    """
    Blends attribute score and scenario score based on availability.
    - When only scenario score exists -> return scenario_score
    - When only attribute score exists -> return attr_score
    - When both exist -> return weighted average
    - When neither exists -> return None
    """
    if attr_score is not None and scenario_score is not None:
        blended = (attr_score * attr_weight) + (scenario_score * scenario_weight)
        return round(blended, 2)
    elif attr_score is not None:
        return round(attr_score, 2)
    elif scenario_score is not None:
        return round(scenario_score, 2)
    else:
        return None


def _evaluate_scenario_dimension(
    evaluator: UserProfile, candidate: UserProfile, target_dimension: str
) -> Tuple[Optional[float], List[str]]:
    """
    Evaluates scenario-based compatibility for target dimension with scenario integrity and importance weighting.

    Semantics:
    - Directional comparison checks if Candidate's self-reported behavior (`normalized_preference`)
      matches Evaluator's explicitly stated expectation for partner (`expected_partner_preference`).
    - If Evaluator has no explicitly stated `expected_partner_preference` for that scenario, no comparison is made.
    - Scenarios with importance == 0.0 are ignored.
    - Scenarios with mismatched target_dimension definition are ignored.
    """
    eval_scenarios = [
        s for s in evaluator.scenarios
        if s.target_dimension == target_dimension and s.importance > 0.0
    ]
    cand_scenarios = [
        s for s in candidate.scenarios
        if s.target_dimension == target_dimension and s.importance > 0.0
    ]

    if not eval_scenarios or not cand_scenarios:
        return None, []

    cand_scen_map = {s.scenario_id: s for s in cand_scenarios}

    total_weight = 0.0
    weighted_score = 0.0
    evidence_lines: List[str] = []

    for e_scen in eval_scenarios:
        if e_scen.scenario_id in cand_scen_map:
            c_scen = cand_scen_map[e_scen.scenario_id]

            # Verify scenario definition integrity (must share target dimension)
            if c_scen.target_dimension != e_scen.target_dimension:
                continue

            # Explicit expectation check only - NO fallback assumption
            expected_partner_pref = normalize_str(e_scen.expected_partner_preference)
            actual_cand_behavior = normalize_str(c_scen.normalized_preference)

            if expected_partner_pref is None:
                # Evaluator did not state an explicit partner expectation for this scenario
                continue

            w = e_scen.importance
            if actual_cand_behavior == expected_partner_pref:
                match_score = 100.0
                outcome_text = "ALIGNS"
            else:
                match_score = 0.0
                outcome_text = "DIVERGES"

            weighted_score += match_score * w
            total_weight += w

            raw_cand_evidence = f" (raw: '{c_scen.raw_answer}')" if c_scen.raw_answer else ""
            evidence_lines.append(
                f"[{target_dimension}] Scenario '{e_scen.scenario_id}' {outcome_text}: "
                f"Candidate behavior '{c_scen.normalized_preference}'{raw_cand_evidence} "
                f"vs Evaluator expected '{e_scen.expected_partner_preference}' (importance: {w})."
            )

    if total_weight <= 0.0:
        return None, []

    final_scenario_score = weighted_score / total_weight
    return round(final_scenario_score, 2), evidence_lines
