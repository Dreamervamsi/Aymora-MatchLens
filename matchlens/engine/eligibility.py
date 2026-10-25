"""
Mutual eligibility filtering for MatchLens.
Checks mandatory dealbreakers across both directions before scoring.
Supports three explicit states: 'eligible', 'ineligible', and 'pending_information'.
"""

from typing import List, Optional, Tuple, Set
from matchlens.models.profile import UserProfile
from matchlens.models.scoring import EligibilityStatus


def normalize_str(val: Optional[str]) -> Optional[str]:
    """
    Normalizes string values for consistent comparison.
    Strips whitespace and converts to lowercase. Returns None for empty strings.
    """
    if val is None:
        return None
    cleaned = val.strip().lower()
    return cleaned if cleaned else None


def normalize_str_list(vals: Optional[List[str]]) -> Optional[List[str]]:
    """
    Normalizes a list of string values.
    """
    if vals is None:
        return None
    cleaned_list = [normalize_str(v) for v in vals if normalize_str(v) is not None]
    return cleaned_list if cleaned_list else None


def _check_directional_eligibility(
    evaluator: UserProfile, candidate: UserProfile, direction_label: str
) -> Tuple[List[str], List[str]]:
    """
    Checks if Candidate satisfies Evaluator's mandatory expectations and dealbreakers.
    Returns (ineligible_reasons, pending_reasons).
    """
    ineligible_reasons: List[str] = []
    pending_reasons: List[str] = []

    e_db = evaluator.dealbreakers
    e_exp = evaluator.expectations
    c_attr = candidate.attributes

    # Self-matching rejection
    if evaluator.user_id == candidate.user_id:
        ineligible_reasons.append("Self-matching is disallowed: a user cannot match with themselves.")
        return ineligible_reasons, pending_reasons

    # Blocked user check
    if candidate.user_id in e_db.blocked_user_ids:
        ineligible_reasons.append(f"{evaluator.user_id} has explicitly blocked {candidate.user_id}.")

    # Relationship Intentions check
    if e_db.strict_intention_match:
        norm_desired_intentions = normalize_str_list(e_exp.desired_intentions)
        if norm_desired_intentions:
            norm_cand_intent = normalize_str(c_attr.relationship_intent)
            if norm_cand_intent is None:
                pending_reasons.append(
                    f"{direction_label}: Candidate's relationship intent is unknown/missing."
                )
            elif norm_cand_intent not in norm_desired_intentions:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's relationship intent '{c_attr.relationship_intent}' "
                    f"is not in Evaluator's acceptable intentions {e_exp.desired_intentions}."
                )

    # Gender match check
    if e_db.strict_gender_match:
        norm_acc_genders = normalize_str_list(e_exp.acceptable_genders)
        if norm_acc_genders and "any" not in norm_acc_genders and "all" not in norm_acc_genders:
            norm_cand_gender = normalize_str(c_attr.gender)
            if norm_cand_gender is None:
                pending_reasons.append(
                    f"{direction_label}: Candidate's gender is unknown/missing."
                )
            elif norm_cand_gender not in norm_acc_genders:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's gender '{c_attr.gender}' "
                    f"is not in Evaluator's acceptable genders {e_exp.acceptable_genders}."
                )

    # Age range check
    if e_db.strict_age_range:
        if c_attr.age is None:
            pending_reasons.append(
                f"{direction_label}: Candidate's age is unknown/missing."
            )
        else:
            if e_exp.min_age is not None and c_attr.age < e_exp.min_age:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's age ({c_attr.age}) is below Evaluator's minimum age ({e_exp.min_age})."
                )
            if e_exp.max_age is not None and c_attr.age > e_exp.max_age:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's age ({c_attr.age}) is above Evaluator's maximum age ({e_exp.max_age})."
                )

    # Smoking dealbreaker
    if e_db.smoking_dealbreaker:
        norm_acc_smoking = normalize_str_list(e_exp.acceptable_smoking)
        if norm_acc_smoking:
            norm_cand_smoking = normalize_str(c_attr.smoking)
            if norm_cand_smoking is None:
                pending_reasons.append(
                    f"{direction_label}: Candidate's smoking habit is unknown/missing."
                )
            elif norm_cand_smoking not in norm_acc_smoking:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's smoking habit '{c_attr.smoking}' "
                    f"violates Evaluator's smoking dealbreaker {e_exp.acceptable_smoking}."
                )

    # Children dealbreaker
    if e_db.children_dealbreaker:
        norm_acc_children = normalize_str_list(e_exp.desired_wants_children)
        if norm_acc_children:
            norm_cand_children = normalize_str(c_attr.wants_children)
            if norm_cand_children is None:
                pending_reasons.append(
                    f"{direction_label}: Candidate's stance on children is unknown/missing."
                )
            elif norm_cand_children not in norm_acc_children:
                ineligible_reasons.append(
                    f"{direction_label}: Candidate's stance on children '{c_attr.wants_children}' "
                    f"violates Evaluator's children dealbreaker {e_exp.desired_wants_children}."
                )

    return ineligible_reasons, pending_reasons


def check_mutual_eligibility(user_a: UserProfile, user_b: UserProfile) -> Tuple[EligibilityStatus, List[str]]:
    """
    Evaluates mutual mandatory requirements between User A and User B.
    Returns (eligibility_status, reasons).
    Status will be:
    - 'ineligible': Hard dealbreaker violation or self-matching.
    - 'pending_information': Required mandatory attribute is missing/unknown.
    - 'eligible': All mandatory dealbreaker requirements are satisfied.
    """
    if user_a.user_id == user_b.user_id:
        return "ineligible", ["Self-matching is disallowed: user_id cannot match with itself."]

    a_to_b_inelig, a_to_b_pend = _check_directional_eligibility(user_a, user_b, f"{user_a.user_id} -> {user_b.user_id}")
    b_to_a_inelig, b_to_a_pend = _check_directional_eligibility(user_b, user_a, f"{user_b.user_id} -> {user_a.user_id}")

    all_ineligible = a_to_b_inelig + b_to_a_inelig
    all_pending = a_to_b_pend + b_to_a_pend

    if all_ineligible:
        return "ineligible", all_ineligible
    elif all_pending:
        return "pending_information", all_pending
    else:
        return "eligible", []
