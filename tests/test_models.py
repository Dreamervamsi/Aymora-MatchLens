import pytest
from pydantic import ValidationError
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    Dealbreakers,
    DimensionWeights,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.models.scoring import MatchResult


def test_default_weights_validation():
    weights = DimensionWeights()
    assert weights.core_values == 0.30
    assert weights.relationship_intentions == 0.25
    assert weights.lifestyle_compatibility == 0.20
    assert weights.communication_preferences == 0.15
    assert weights.shared_interests == 0.10


def test_zero_total_weights_rejection():
    with pytest.raises(ValidationError):
        DimensionWeights(
            core_values=0.0,
            relationship_intentions=0.0,
            lifestyle_compatibility=0.0,
            communication_preferences=0.0,
            shared_interests=0.0,
        )


def test_non_finite_weights_rejection():
    with pytest.raises(ValidationError):
        DimensionWeights(core_values=float("nan"))
    with pytest.raises(ValidationError):
        DimensionWeights(core_values=float("inf"))


def test_invalid_target_dimension_rejection():
    with pytest.raises(ValidationError):
        ScenarioResponse(
            scenario_id="scen_01",
            target_dimension="invalid_dimension_name",  # Not in SupportedDimension
            normalized_preference="opt_a",
        )


def test_age_min_exceeds_max_rejection():
    with pytest.raises(ValidationError):
        PartnerPreferences(min_age=40, max_age=30)


def test_scenario_perspective_and_expectation():
    scen = ScenarioResponse(
        scenario_id="scen_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="cool_down_first",
        expected_partner_preference="discuss_immediately",
    )
    assert scen.perspective == "self_behavior"
    assert scen.expected_partner_preference == "discuss_immediately"


def test_duplicate_scenario_ids_rejection():
    scen1 = ScenarioResponse(
        scenario_id="conflict_01",
        target_dimension="communication_preferences",
        normalized_preference="cool_down_first",
    )
    scen2 = ScenarioResponse(
        scenario_id="conflict_01",  # Duplicate ID
        target_dimension="lifestyle_compatibility",
        normalized_preference="early_bird",
    )
    with pytest.raises(ValidationError):
        UserProfile(
            user_id="user_1",
            scenarios=[scen1, scen2],
        )


def test_user_profile_creation():
    user = UserProfile(
        user_id="user_123",
        attributes=UserAttributes(
            age=28,
            gender="man",
            relationship_intent="long_term",
            core_values=["honesty", "family"],
            interests=["hiking", "cooking"],
        ),
        expectations=PartnerPreferences(
            min_age=24,
            max_age=32,
            acceptable_genders=["woman"],
            desired_intentions=["long_term"],
        ),
        dealbreakers=Dealbreakers(
            blocked_user_ids=["user_999"]
        ),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                raw_answer="I prefer taking an hour to cool down before talking.",
            )
        ]
    )

    assert user.user_id == "user_123"
    assert user.attributes.age == 28
    assert user.expectations.min_age == 24
    assert len(user.scenarios) == 1
    assert user.scenarios[0].normalized_preference == "cool_down_first"


def test_invalid_age():
    with pytest.raises(ValidationError):
        UserAttributes(age=15)  # Under minimum age 18

