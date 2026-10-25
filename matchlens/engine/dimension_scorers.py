"""
Pure deterministic dimension scoring and scenario alignment functions for MatchLens.
Calculates score [0.0 - 100.0], human-readable shared/gap/scenario factors,
and structured EvidenceRecords for full traceability.

NOTE ON SCENARIO COMPATIBILITY HEURISTIC:
Scenario alignment uses a rule-based categorical similarity heuristic comparing
a candidate's self-reported scenario behavior with an evaluator's explicitly stated
partner expectation. This provides deterministic, traceable alignment indicators for matching,
and is NOT a scientifically validated psychological diagnosis or behavioral model.
"""

from typing import List, Optional, Tuple, Set, Dict, Any
from matchlens.models.profile import UserProfile
from matchlens.models.scenario import ScenarioResponse
from matchlens.models.scoring import EvidenceRecord
from matchlens.engine.eligibility import normalize_str, normalize_str_list
from matchlens.config import (
    DIMENSION_CORE_VALUES,
    DIMENSION_RELATIONSHIP_INTENTIONS,
    DIMENSION_LIFESTYLE,
    DIMENSION_COMMUNICATION,
    DIMENSION_INTERESTS,
)


def _is_unrestricted(options: Optional[List[str]]) -> bool:
    """
    Checks if a preference list is explicitly unrestricted ('any', 'all', or empty list []).
    """
    if options is None:
        return False
    if len(options) == 0:
        return True
    norm_options = {o.lower().strip() for o in options}
    return "any" in norm_options or "all" in norm_options


def score_core_values(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str], List[EvidenceRecord]]:
    """
    Evaluates core values compatibility.
    Evaluator desired_values vs Candidate core_values.
    """
    records: List[EvidenceRecord] = []
    desired = evaluator.expectations.desired_values
    cand_values = candidate.attributes.core_values

    attr_score = None
    shared_factors = []
    gap_factors = []

    if desired is not None and cand_values is not None:
        if _is_unrestricted(desired):
            attr_score = 100.0
            shared_factors.append("[core_values] Evaluator is open to any core values.")
            records.append(
                EvidenceRecord(
                    dimension_name=DIMENSION_CORE_VALUES,
                    source_type="attribute",
                    source_id="core_values",
                    evaluator_expectation=desired,
                    candidate_value=cand_values,
                    outcome="match",
                    score_impact=100.0,
                    is_scoring_factor=True,
                )
            )
        else:
            norm_desired = normalize_str_list(desired) or []
            norm_cand = normalize_str_list(cand_values) or []
            desired_set = set(norm_desired)
            cand_set = set(norm_cand)

            if desired_set:
                matched = desired_set.intersection(cand_set)
                missing = desired_set.difference(cand_set)

                attr_score = (len(matched) / len(desired_set)) * 100.0

                shared_factors = [f"[core_values] Shared core value: '{m}'" for m in sorted(matched)]
                gap_factors = [f"[core_values] Desired value '{m}' missing in candidate profile" for m in sorted(missing)]

                outcome = "match" if attr_score == 100.0 else ("partial" if attr_score > 0 else "mismatch")
                records.append(
                    EvidenceRecord(
                        dimension_name=DIMENSION_CORE_VALUES,
                        source_type="attribute",
                        source_id="core_values",
                        evaluator_expectation=desired,
                        candidate_value=cand_values,
                        outcome=outcome,
                        score_impact=attr_score,
                        is_scoring_factor=True,
                    )
                )

    scenario_score, scenario_evidence, scenario_records = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_CORE_VALUES
    )
    records.extend(scenario_records)

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared_factors, gap_factors, scenario_evidence, records


def score_relationship_intentions(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str], List[EvidenceRecord]]:
    """
    Evaluates relationship intentions compatibility.
    Candidate relationship_intent vs Evaluator desired_intentions.
    """
    records: List[EvidenceRecord] = []
    desired_intentions = evaluator.expectations.desired_intentions
    cand_intent = candidate.attributes.relationship_intent

    attr_score = None
    shared = []
    gaps = []

    if desired_intentions is not None and cand_intent is not None:
        if _is_unrestricted(desired_intentions):
            attr_score = 100.0
            shared = ["[relationship_intentions] Evaluator is open to any relationship intention."]
            records.append(
                EvidenceRecord(
                    dimension_name=DIMENSION_RELATIONSHIP_INTENTIONS,
                    source_type="attribute",
                    source_id="relationship_intent",
                    evaluator_expectation=desired_intentions,
                    candidate_value=cand_intent,
                    outcome="match",
                    score_impact=100.0,
                    is_scoring_factor=True,
                )
            )
        else:
            norm_desired = normalize_str_list(desired_intentions) or []
            norm_c_intent = normalize_str(cand_intent)
            if norm_c_intent in norm_desired:
                attr_score = 100.0
                shared = [f"[relationship_intentions] Candidate's intent '{cand_intent}' matches evaluator's expectations"]
                outcome = "match"
            else:
                attr_score = 0.0
                gaps = [f"[relationship_intentions] Candidate's intent '{cand_intent}' differs from evaluator's expectations {desired_intentions}"]
                outcome = "mismatch"

            records.append(
                EvidenceRecord(
                    dimension_name=DIMENSION_RELATIONSHIP_INTENTIONS,
                    source_type="attribute",
                    source_id="relationship_intent",
                    evaluator_expectation=desired_intentions,
                    candidate_value=cand_intent,
                    outcome=outcome,
                    score_impact=attr_score,
                    is_scoring_factor=True,
                )
            )

    scenario_score, scenario_evidence, scenario_records = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_RELATIONSHIP_INTENTIONS
    )
    records.extend(scenario_records)

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared, gaps, scenario_evidence, records


def score_lifestyle(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str], List[EvidenceRecord]]:
    """
    Evaluates lifestyle compatibility across sub-attributes and scenarios.
    """
    records: List[EvidenceRecord] = []
    exp = evaluator.expectations
    c_attr = candidate.attributes

    sub_scores = []
    shared_factors = []
    gap_factors = []

    # 1. Smoking
    if exp.acceptable_smoking is not None and c_attr.smoking is not None:
        if _is_unrestricted(exp.acceptable_smoking):
            sub_scores.append(100.0)
            shared_factors.append("[lifestyle_compatibility] Open to any smoking habit.")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="smoking",
                evaluator_expectation=exp.acceptable_smoking, candidate_value=c_attr.smoking, outcome="match", score_impact=100.0
            ))
        else:
            norm_acc_smoking = normalize_str_list(exp.acceptable_smoking) or []
            norm_c_smoking = normalize_str(c_attr.smoking)
            if norm_c_smoking in norm_acc_smoking:
                sub_scores.append(100.0)
                shared_factors.append(f"[lifestyle_compatibility] Acceptable smoking habit: '{c_attr.smoking}'")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="smoking",
                    evaluator_expectation=exp.acceptable_smoking, candidate_value=c_attr.smoking, outcome="match", score_impact=100.0
                ))
            else:
                sub_scores.append(0.0)
                gap_factors.append(f"[lifestyle_compatibility] Smoking habit '{c_attr.smoking}' not in acceptable options {exp.acceptable_smoking}")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="smoking",
                    evaluator_expectation=exp.acceptable_smoking, candidate_value=c_attr.smoking, outcome="mismatch", score_impact=0.0
                ))

    # 2. Drinking
    if exp.acceptable_drinking is not None and c_attr.drinking is not None:
        if _is_unrestricted(exp.acceptable_drinking):
            sub_scores.append(100.0)
            shared_factors.append("[lifestyle_compatibility] Open to any drinking habit.")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="drinking",
                evaluator_expectation=exp.acceptable_drinking, candidate_value=c_attr.drinking, outcome="match", score_impact=100.0
            ))
        else:
            norm_acc_drinking = normalize_str_list(exp.acceptable_drinking) or []
            norm_c_drinking = normalize_str(c_attr.drinking)
            if norm_c_drinking in norm_acc_drinking:
                sub_scores.append(100.0)
                shared_factors.append(f"[lifestyle_compatibility] Acceptable drinking habit: '{c_attr.drinking}'")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="drinking",
                    evaluator_expectation=exp.acceptable_drinking, candidate_value=c_attr.drinking, outcome="match", score_impact=100.0
                ))
            else:
                sub_scores.append(0.0)
                gap_factors.append(f"[lifestyle_compatibility] Drinking habit '{c_attr.drinking}' not in acceptable options {exp.acceptable_drinking}")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="drinking",
                    evaluator_expectation=exp.acceptable_drinking, candidate_value=c_attr.drinking, outcome="mismatch", score_impact=0.0
                ))

    # 3. Children stance
    if exp.desired_wants_children is not None and c_attr.wants_children is not None:
        if _is_unrestricted(exp.desired_wants_children):
            sub_scores.append(100.0)
            shared_factors.append("[lifestyle_compatibility] Open to any position on children.")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="wants_children",
                evaluator_expectation=exp.desired_wants_children, candidate_value=c_attr.wants_children, outcome="match", score_impact=100.0
            ))
        else:
            norm_acc_children = normalize_str_list(exp.desired_wants_children) or []
            norm_c_children = normalize_str(c_attr.wants_children)
            if norm_c_children in norm_acc_children:
                sub_scores.append(100.0)
                shared_factors.append(f"[lifestyle_compatibility] Aligned position on children: '{c_attr.wants_children}'")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="wants_children",
                    evaluator_expectation=exp.desired_wants_children, candidate_value=c_attr.wants_children, outcome="match", score_impact=100.0
                ))
            else:
                sub_scores.append(0.0)
                gap_factors.append(f"[lifestyle_compatibility] Stance on children '{c_attr.wants_children}' not in preferred options {exp.desired_wants_children}")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_LIFESTYLE, source_type="attribute", source_id="wants_children",
                    evaluator_expectation=exp.desired_wants_children, candidate_value=c_attr.wants_children, outcome="mismatch", score_impact=0.0
                ))

    attr_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    scenario_score, scenario_evidence, scenario_records = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_LIFESTYLE
    )
    records.extend(scenario_records)

    final_score = _blend_dimension_scores(attr_score, scenario_score, attr_weight=0.6, scenario_weight=0.4)
    return final_score, shared_factors, gap_factors, scenario_evidence, records


def score_communication(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str], List[EvidenceRecord]]:
    """
    Evaluates communication preferences & conflict resolution.
    """
    records: List[EvidenceRecord] = []
    exp = evaluator.expectations
    c_attr = candidate.attributes

    sub_scores = []
    shared_factors = []
    gap_factors = []

    # 1. Communication style
    if exp.desired_communication_styles is not None and c_attr.communication_style is not None:
        if _is_unrestricted(exp.desired_communication_styles):
            sub_scores.append(100.0)
            shared_factors.append("[communication_preferences] Open to any communication style.")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="communication_style",
                evaluator_expectation=exp.desired_communication_styles, candidate_value=c_attr.communication_style, outcome="match", score_impact=100.0
            ))
        else:
            norm_desired_styles = normalize_str_list(exp.desired_communication_styles) or []
            norm_c_style = normalize_str(c_attr.communication_style)
            if norm_c_style in norm_desired_styles:
                sub_scores.append(100.0)
                shared_factors.append(f"[communication_preferences] Preferred communication style: '{c_attr.communication_style}'")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="communication_style",
                    evaluator_expectation=exp.desired_communication_styles, candidate_value=c_attr.communication_style, outcome="match", score_impact=100.0
                ))
            else:
                sub_scores.append(25.0)
                gap_factors.append(f"[communication_preferences] Communication style '{c_attr.communication_style}' differs from preferred styles {exp.desired_communication_styles}")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="communication_style",
                    evaluator_expectation=exp.desired_communication_styles, candidate_value=c_attr.communication_style, outcome="partial", score_impact=25.0
                ))

    # 2. Conflict resolution
    if exp.desired_conflict_resolutions is not None and c_attr.conflict_resolution is not None:
        if _is_unrestricted(exp.desired_conflict_resolutions):
            sub_scores.append(100.0)
            shared_factors.append("[communication_preferences] Open to any conflict resolution style.")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="conflict_resolution",
                evaluator_expectation=exp.desired_conflict_resolutions, candidate_value=c_attr.conflict_resolution, outcome="match", score_impact=100.0
            ))
        else:
            norm_desired_conflicts = normalize_str_list(exp.desired_conflict_resolutions) or []
            norm_c_conflict = normalize_str(c_attr.conflict_resolution)
            if norm_c_conflict in norm_desired_conflicts:
                sub_scores.append(100.0)
                shared_factors.append(f"[communication_preferences] Aligned conflict resolution style: '{c_attr.conflict_resolution}'")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="conflict_resolution",
                    evaluator_expectation=exp.desired_conflict_resolutions, candidate_value=c_attr.conflict_resolution, outcome="match", score_impact=100.0
                ))
            else:
                sub_scores.append(25.0)
                gap_factors.append(f"[communication_preferences] Conflict resolution style '{c_attr.conflict_resolution}' differs from preferred styles {exp.desired_conflict_resolutions}")
                records.append(EvidenceRecord(
                    dimension_name=DIMENSION_COMMUNICATION, source_type="attribute", source_id="conflict_resolution",
                    evaluator_expectation=exp.desired_conflict_resolutions, candidate_value=c_attr.conflict_resolution, outcome="partial", score_impact=25.0
                ))

    attr_score = sum(sub_scores) / len(sub_scores) if sub_scores else None

    scenario_score, scenario_evidence, scenario_records = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_COMMUNICATION
    )
    records.extend(scenario_records)

    final_score = _blend_dimension_scores(attr_score, scenario_score, attr_weight=0.5, scenario_weight=0.5)
    return final_score, shared_factors, gap_factors, scenario_evidence, records


def score_shared_interests(
    evaluator: UserProfile, candidate: UserProfile
) -> Tuple[Optional[float], List[str], List[str], List[str], List[EvidenceRecord]]:
    """
    Evaluates shared interests using Jaccard similarity.
    """
    records: List[EvidenceRecord] = []
    eval_interests = normalize_str_list(evaluator.attributes.interests)
    cand_interests = normalize_str_list(candidate.attributes.interests)

    attr_score = None
    shared_factors = []
    gap_factors = []

    if eval_interests is not None and cand_interests is not None:
        e_set = set(eval_interests)
        c_set = set(cand_interests)

        intersection = e_set.intersection(c_set)
        union = e_set.union(c_set)

        if union:
            attr_score = (len(intersection) / len(union)) * 100.0
            shared_factors = [f"[shared_interests] Shared interest: '{i}'" for i in sorted(intersection)]

            outcome = "match" if attr_score == 100.0 else ("partial" if attr_score > 0 else "mismatch")
            records.append(EvidenceRecord(
                dimension_name=DIMENSION_INTERESTS, source_type="attribute", source_id="interests",
                evaluator_expectation=evaluator.attributes.interests, candidate_value=candidate.attributes.interests,
                outcome=outcome, score_impact=attr_score
            ))

    scenario_score, scenario_evidence, scenario_records = _evaluate_scenario_dimension(
        evaluator, candidate, DIMENSION_INTERESTS
    )
    records.extend(scenario_records)

    final_score = _blend_dimension_scores(attr_score, scenario_score)
    return final_score, shared_factors, gap_factors, scenario_evidence, records


def _blend_dimension_scores(
    attr_score: Optional[float],
    scenario_score: Optional[float],
    attr_weight: float = 0.5,
    scenario_weight: float = 0.5,
) -> Optional[float]:
    """
    Blends attribute score and scenario score based on availability.
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
) -> Tuple[Optional[float], List[str], List[EvidenceRecord]]:
    """
    Evaluates scenario-based compatibility for target dimension with scenario integrity and importance weighting.

    Perspective Correctness Rules:
    - Candidate response represents candidate's self-reported behavior ONLY when c_scen.perspective == "self_behavior".
      Responses where c_scen.perspective == "partner_expectation" describe candidate's partner wishes, NOT their own behavior.
    - Evaluator's expectation comes from e_scen.expected_partner_preference (or e_scen.normalized_preference when e_scen.perspective == "partner_expectation").
    """
    records: List[EvidenceRecord] = []
    eval_scenarios = [
        s for s in evaluator.scenarios
        if s.target_dimension == target_dimension and s.importance > 0.0
    ]
    cand_scenarios = [
        s for s in candidate.scenarios
        if s.target_dimension == target_dimension and s.importance > 0.0
    ]

    if not eval_scenarios or not cand_scenarios:
        return None, [], []

    cand_scen_map = {s.scenario_id: s for s in cand_scenarios}

    total_weight = 0.0
    weighted_score = 0.0
    evidence_lines: List[str] = []

    for e_scen in eval_scenarios:
        if e_scen.scenario_id in cand_scen_map:
            c_scen = cand_scen_map[e_scen.scenario_id]

            if c_scen.target_dimension != e_scen.target_dimension:
                continue

            # Check candidate perspective: must be self_behavior to represent actual candidate behavior
            if c_scen.perspective != "self_behavior":
                continue

            # Determine evaluator's partner expectation
            if e_scen.expected_partner_preference:
                expected_partner_pref = normalize_str(e_scen.expected_partner_preference)
            elif e_scen.perspective == "partner_expectation":
                expected_partner_pref = normalize_str(e_scen.normalized_preference)
            else:
                expected_partner_pref = None

            actual_cand_behavior = normalize_str(c_scen.normalized_preference)

            if expected_partner_pref is None:
                continue

            w = e_scen.importance
            if actual_cand_behavior == expected_partner_pref:
                match_score = 100.0
                outcome_text = "ALIGNS"
                outcome_key = "match"
            else:
                match_score = 0.0
                outcome_text = "DIVERGES"
                outcome_key = "mismatch"

            weighted_score += match_score * w
            total_weight += w

            raw_cand_evidence = f" (raw: '{c_scen.raw_answer}')" if c_scen.raw_answer else ""
            evidence_lines.append(
                f"[{target_dimension}] Scenario '{e_scen.scenario_id}' {outcome_text}: "
                f"Candidate behavior '{c_scen.normalized_preference}'{raw_cand_evidence} "
                f"vs Evaluator expected '{expected_partner_pref}' (importance: {w})."
            )

            records.append(
                EvidenceRecord(
                    dimension_name=target_dimension,
                    source_type="scenario",
                    source_id=e_scen.scenario_id,
                    evaluator_expectation=expected_partner_pref,
                    candidate_value=c_scen.normalized_preference,
                    outcome=outcome_key,
                    score_impact=match_score,
                    is_scoring_factor=True,
                )
            )

    if total_weight <= 0.0:
        return None, [], []

    final_scenario_score = weighted_score / total_weight
    return round(final_scenario_score, 2), evidence_lines, records
