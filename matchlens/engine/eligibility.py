"""
Mutual eligibility filtering for MatchLens.
Checks mandatory dealbreakers across both directions before scoring.
"""

from typing import List, Tuple
from matchlens.models.profile import UserProfile


def _check_directional_eligibility(
    evaluator: UserProfile, candidate: UserProfile, direction_label: str
) -> List[str]:
    """
    Checks if Candidate satisfies Evaluator's mandatory expectations and dealbreakers.
    """
    reasons: List[str] = []
    e_db = evaluator.dealbreakers
    e_exp = evaluator.expectations
    c_attr = candidate.attributes

    # Blocked user check
    if candidate.user_id in e_db.blocked_user_ids:
        reasons.append(f"{evaluator.user_id} has explicitly blocked {candidate.user_id}.")

    # Relationship Intentions check
    if e_db.strict_intention_match:
        if e_exp.desired_intentions is not None and len(e_exp.desired_intentions) > 0:
            if c_attr.relationship_intent is not None:
                if c_attr.relationship_intent not in e_exp.desired_intentions:
                    reasons.append(
                        f"{direction_label}: Candidate's relationship intent '{c_attr.relationship_intent}' "
                        f"is not in Evaluator's acceptable intentions {e_exp.desired_intentions}."
                    )

    # Gender match check
    if e_db.strict_gender_match:
        if e_exp.acceptable_genders is not None and len(e_exp.acceptable_genders) > 0:
            if "any" not in e_exp.acceptable_genders and "all" not in e_exp.acceptable_genders:
                if c_attr.gender is not None:
                    if c_attr.gender not in e_exp.acceptable_genders:
                        reasons.append(
                            f"{direction_label}: Candidate's gender '{c_attr.gender}' "
                            f"is not in Evaluator's acceptable genders {e_exp.acceptable_genders}."
                        )

    # Age range check
    if e_db.strict_age_range:
        if c_attr.age is not None:
            if e_exp.min_age is not None and c_attr.age < e_exp.min_age:
                reasons.append(
                    f"{direction_label}: Candidate's age ({c_attr.age}) is below Evaluator's minimum age ({e_exp.min_age})."
                )
            if e_exp.max_age is not None and c_attr.age > e_exp.max_age:
                reasons.append(
                    f"{direction_label}: Candidate's age ({c_attr.age}) is above Evaluator's maximum age ({e_exp.max_age})."
                )

    # Smoking dealbreaker
    if e_db.smoking_dealbreaker:
        if e_exp.acceptable_smoking is not None and len(e_exp.acceptable_smoking) > 0:
            if c_attr.smoking is not None:
                if c_attr.smoking not in e_exp.acceptable_smoking:
                    reasons.append(
                        f"{direction_label}: Candidate's smoking habit '{c_attr.smoking}' "
                        f"violates Evaluator's smoking dealbreaker {e_exp.acceptable_smoking}."
                    )

    # Children dealbreaker
    if e_db.children_dealbreaker:
        if e_exp.desired_wants_children is not None and len(e_exp.desired_wants_children) > 0:
            if c_attr.wants_children is not None:
                if c_attr.wants_children not in e_exp.desired_wants_children:
                    reasons.append(
                        f"{direction_label}: Candidate's stance on children '{c_attr.wants_children}' "
                        f"violates Evaluator's children dealbreaker {e_exp.desired_wants_children}."
                    )

    return reasons


def check_mutual_eligibility(user_a: UserProfile, user_b: UserProfile) -> Tuple[bool, List[str]]:
    """
    Evaluates mutual mandatory requirements between User A and User B.
    Returns (is_eligible, ineligibility_reasons).
    """
    a_to_b_reasons = _check_directional_eligibility(user_a, user_b, f"{user_a.user_id} -> {user_b.user_id}")
    b_to_a_reasons = _check_directional_eligibility(user_b, user_a, f"{user_b.user_id} -> {user_a.user_id}")

    all_reasons = a_to_b_reasons + b_to_a_reasons
    is_eligible = len(all_reasons) == 0

    return is_eligible, all_reasons
