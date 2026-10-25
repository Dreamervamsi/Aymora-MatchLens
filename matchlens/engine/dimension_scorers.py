from typing import List, Optional, Tuple, Set
from matchlens.models.profile import UserProfile
from matchlens.models.scenario import ScenarioResponse
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
    desired = evaluator.expectations.desired_values
    cand_values = candidate.attributes.core_values

    if desired is None or cand_values is None:
        return None, [], [], []

    desired_set = {v.lower().strip() for v in desired}
    cand_set = {v.lower().strip() for v in cand_values}

    if not desired_set:
        return None, [], [], []

    matched = desired_set.intersection(cand_set)
    missing = desired_set.difference(cand_set)

    score = (len(matched) / len(desired_set)) * 100.0

    shared_factors = [f"Shared core value: '{m}'" for m in sorted(matched)]
    gap_factors = [f"Desired value '{m}' missing in candidate" for m in sorted(missing)]

    # Scenario evidence integration for core_values
    scenario_evidence = _evaluate_scenario_alignment(evaluator, candidate, DIMENSION_CORE_VALUES)

    return round(score, 2), shared_factors, gap_factors, scenario_evidence


def score_relationship_intentions(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    """
    Evaluates relationship intentions compatibility.
    Candidate relationship_intent vs Evaluator desired_intentions.
    """
    desired_intentions = evaluator.expectations.desired_intentions
    cand_intent = candidate.attributes.relationship_intent

    if desired_intentions is None or cand_intent is None:
        return None, [], [], []

    desired_set = {i.lower().strip() for i in desired_intentions}
    c_intent_norm = cand_intent.lower().strip()

    if not desired_set:
        return None, [], [], []

    if c_intent_norm in desired_set:
        score = 100.0
        shared = [f"Candidate's intent '{cand_intent}' matches requested intentions"]
        gaps = []
    else:
        score = 0.0
        shared = []
        gaps = [f"Candidate's intent '{cand_intent}' differs from desired intentions {desired_intentions}"]

    scenario_evidence = _evaluate_scenario_alignment(evaluator, candidate, DIMENSION_RELATIONSHIP_INTENTIONS)

    return round(score, 2), shared, gaps, scenario_evidence


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
    if exp.acceptable_smoking is not None and len(exp.acceptable_smoking) > 0 and c_attr.smoking is not None:
        acc_smoking = {s.lower() for s in exp.acceptable_smoking}
        if c_attr.smoking.lower() in acc_smoking:
            sub_scores.append(100.0)
            shared_factors.append(f"Acceptable smoking habit: '{c_attr.smoking}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"Smoking habit '{c_attr.smoking}' not in acceptable choices {exp.acceptable_smoking}")

    # 2. Drinking
    if exp.acceptable_drinking is not None and len(exp.acceptable_drinking) > 0 and c_attr.drinking is not None:
        acc_drinking = {d.lower() for d in exp.acceptable_drinking}
        if c_attr.drinking.lower() in acc_drinking:
            sub_scores.append(100.0)
            shared_factors.append(f"Acceptable drinking habit: '{c_attr.drinking}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"Drinking habit '{c_attr.drinking}' not in acceptable choices {exp.acceptable_drinking}")

    # 3. Children stance
    if exp.desired_wants_children is not None and len(exp.desired_wants_children) > 0 and c_attr.wants_children is not None:
        acc_kids = {k.lower() for k in exp.desired_wants_children}
        if c_attr.wants_children.lower() in acc_kids:
            sub_scores.append(100.0)
            shared_factors.append(f"Aligned position on children: '{c_attr.wants_children}'")
        else:
            sub_scores.append(0.0)
            gap_factors.append(f"Children stance '{c_attr.wants_children}' not in desired positions {exp.desired_wants_children}")

    scenario_evidence = _evaluate_scenario_alignment(evaluator, candidate, DIMENSION_LIFESTYLE)

    if not sub_scores and not scenario_evidence:
        return None, [], [], []

    base_score = sum(sub_scores) / len(sub_scores) if sub_scores else 50.0

    # Adjust base score with scenario score if available
    scenario_score = _calculate_scenario_score(evaluator, candidate, DIMENSION_LIFESTYLE)
    if scenario_score is not None:
        final_score = (base_score * 0.6) + (scenario_score * 0.4)
    else:
        final_score = base_score

    return round(final_score, 2), shared_factors, gap_factors, scenario_evidence


def score_communication(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    exp = evaluator.expectations
    c_attr = candidate.attributes

    sub_scores = []
    shared_factors = []
    gap_factors = []

    # 1. Communication style
    if exp.desired_communication_styles is not None and len(exp.desired_communication_styles) > 0 and c_attr.communication_style is not None:
        desired_styles = {s.lower() for s in exp.desired_communication_styles}
        if c_attr.communication_style.lower() in desired_styles:
            sub_scores.append(100.0)
            shared_factors.append(f"Preferred communication style: '{c_attr.communication_style}'")
        else:
            sub_scores.append(25.0)
            gap_factors.append(f"Communication style '{c_attr.communication_style}' differs from preferred styles")

    # 2. Conflict resolution
    if exp.desired_conflict_resolutions is not None and len(exp.desired_conflict_resolutions) > 0 and c_attr.conflict_resolution is not None:
        desired_conflicts = {c.lower() for c in exp.desired_conflict_resolutions}
        if c_attr.conflict_resolution.lower() in desired_conflicts:
            sub_scores.append(100.0)
            shared_factors.append(f"Aligned conflict resolution style: '{c_attr.conflict_resolution}'")
        else:
            sub_scores.append(25.0)
            gap_factors.append(f"Conflict resolution style '{c_attr.conflict_resolution}' differs from preferred styles")

    scenario_evidence = _evaluate_scenario_alignment(evaluator, candidate, DIMENSION_COMMUNICATION)

    if not sub_scores and not scenario_evidence:
        return None, [], [], []

    base_score = sum(sub_scores) / len(sub_scores) if sub_scores else 50.0

    scenario_score = _calculate_scenario_score(evaluator, candidate, DIMENSION_COMMUNICATION)
    if scenario_score is not None:
        final_score = (base_score * 0.5) + (scenario_score * 0.5)
    else:
        final_score = base_score

    return round(final_score, 2), shared_factors, gap_factors, scenario_evidence


def score_shared_interests(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str]]:
    eval_interests = evaluator.attributes.interests
    cand_interests = candidate.attributes.interests

    if eval_interests is None or cand_interests is None:
        return None, [], [], []

    e_set = {i.lower().strip() for i in eval_interests}
    c_set = {i.lower().strip() for i in cand_interests}

    if not e_set or not c_set:
        return None, [], [], []

    intersection = e_set.intersection(c_set)
    union = e_set.union(c_set)

    jaccard_score = (len(intersection) / len(union)) * 100.0

    shared_factors = [f"Shared interest: '{i}'" for i in sorted(intersection)]
    gap_factors = []

    scenario_evidence = _evaluate_scenario_alignment(evaluator, candidate, DIMENSION_INTERESTS)

    return round(jaccard_score, 2), shared_factors, gap_factors, scenario_evidence


def _evaluate_scenario_alignment(
    evaluator: UserProfile, candidate: UserProfile, target_dimension: str
) -> List[str]:
    evidence = []
    eval_scenarios = [s for s in evaluator.scenarios if s.target_dimension == target_dimension]
    cand_scenarios = [s for s in candidate.scenarios if s.target_dimension == target_dimension]

    cand_scen_map = {s.scenario_id: s for s in cand_scenarios}

    for e_scen in eval_scenarios:
        if e_scen.scenario_id in cand_scen_map:
            c_scen = cand_scen_map[e_scen.scenario_id]

            # Compare expectation vs behavior
            expected = e_scen.expected_partner_preference or e_scen.normalized_preference
            actual = c_scen.normalized_preference

            if expected == actual:
                evidence.append(
                    f"Scenario '{e_scen.scenario_id}' match: Candidate response '{actual}' aligns with expectation."
                )
            else:
                evidence.append(
                    f"Scenario '{e_scen.scenario_id}' divergence: Candidate response '{actual}' vs expected '{expected}'."
                )

    return evidence


def _calculate_scenario_score(
    evaluator: UserProfile, candidate: UserProfile, target_dimension: str
) -> Optional[float]:
    eval_scenarios = [s for s in evaluator.scenarios if s.target_dimension == target_dimension]
    cand_scenarios = [s for s in candidate.scenarios if s.target_dimension == target_dimension]

    if not eval_scenarios or not cand_scenarios:
        return None

    cand_scen_map = {s.scenario_id: s for s in cand_scenarios}

    total_weight = 0.0
    weighted_score = 0.0

    for e_scen in eval_scenarios:
        if e_scen.scenario_id in cand_scen_map:
            c_scen = cand_scen_map[e_scen.scenario_id]
            expected = e_scen.expected_partner_preference or e_scen.normalized_preference
            actual = c_scen.normalized_preference

            w = e_scen.importance
            match_score = 100.0 if expected == actual else 0.0

            weighted_score += match_score * w
            total_weight += w

    if total_weight <= 0:
        return None

    return weighted_score / total_weight
