import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    Dealbreakers,
)
from matchlens.engine.eligibility import check_mutual_eligibility


def test_fully_eligible_pair():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(min_age=22, max_age=32, acceptable_genders=["woman"], desired_intentions=["long_term"]),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(age=26, gender="woman", relationship_intent="long_term"),
        expectations=PartnerPreferences(min_age=25, max_age=35, acceptable_genders=["man"], desired_intentions=["long_term"]),
    )

    is_eligible, reasons = check_mutual_eligibility(user_a, user_b)
    assert is_eligible is True
    assert len(reasons) == 0


def test_blocked_user_ineligibility():
    user_a = UserProfile(
        user_id="user_a",
        dealbreakers=Dealbreakers(blocked_user_ids=["user_b"]),
    )
    user_b = UserProfile(user_id="user_b")

    is_eligible, reasons = check_mutual_eligibility(user_a, user_b)
    assert is_eligible is False
    assert any("explicitly blocked" in r for r in reasons)


def test_age_out_of_range_ineligibility():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=25),
        expectations=PartnerPreferences(min_age=30, max_age=40),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(age=22),
    )

    is_eligible, reasons = check_mutual_eligibility(user_a, user_b)
    assert is_eligible is False
    assert any("Candidate's age (22) is below Evaluator's minimum age (30)" in r for r in reasons)


def test_gender_mismatch_ineligibility():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(gender="man"),
        expectations=PartnerPreferences(acceptable_genders=["woman"]),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(gender="man"),
        expectations=PartnerPreferences(acceptable_genders=["man"]),
    )

    is_eligible, reasons = check_mutual_eligibility(user_a, user_b)
    assert is_eligible is False
    assert any("acceptable genders" in r for r in reasons)


def test_smoking_dealbreaker_ineligibility():
    user_a = UserProfile(
        user_id="user_a",
        expectations=PartnerPreferences(acceptable_smoking=["never"]),
        dealbreakers=Dealbreakers(smoking_dealbreaker=True),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(smoking="regularly"),
    )

    is_eligible, reasons = check_mutual_eligibility(user_a, user_b)
    assert is_eligible is False
    assert any("smoking dealbreaker" in r for r in reasons)
