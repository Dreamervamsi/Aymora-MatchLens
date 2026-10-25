import math
import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    DimensionWeights,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.reciprocal import calculate_reciprocal_match


def test_geometric_mean_reciprocal_scoring():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(
            age=28,
            gender="man",
            interests=["reading", "hiking"],
            core_values=["honesty"],
            relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=20,
            max_age=35,
            acceptable_genders=["woman"],
            desired_values=["honesty"],
            desired_intentions=["long_term"],
        ),
        weights=DimensionWeights(
            core_values=0.50,
            relationship_intentions=0.50,
            lifestyle_compatibility=0.0,
            communication_preferences=0.0,
            shared_interests=0.0,
        ),
    )

    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(
            age=26,
            gender="woman",
            interests=["reading"],
            core_values=["honesty"],
            relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=20,
            max_age=35,
            acceptable_genders=["man"],
            desired_values=["honesty", "ambition", "family"],  # User A has 1 of 3 -> 33.33%
            desired_intentions=["long_term"],                  # 100%
        ),
        weights=DimensionWeights(
            core_values=0.50,
            relationship_intentions=0.50,
            lifestyle_compatibility=0.0,
            communication_preferences=0.0,
            shared_interests=0.0,
        ),
    )

    result = calculate_reciprocal_match(user_a, user_b)
    assert result.is_eligible is True
    assert result.eligibility_status == "eligible"
    assert result.directional_a_to_b.directional_score == 100.0
    assert result.directional_b_to_a.directional_score == pytest.approx(66.67, 0.1)

    # sqrt(100 * 66.67) ~ 81.65
    expected_mutual = math.sqrt(100.0 * result.directional_b_to_a.directional_score)
    assert result.mutual_score == pytest.approx(expected_mutual, 0.01)
    assert result.evidence_summary is not None


def test_ineligible_pair_reciprocal_match():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=20),
        expectations=PartnerPreferences(min_age=30),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(age=22),
    )

    result = calculate_reciprocal_match(user_a, user_b)
    assert result.is_eligible is False
    assert result.eligibility_status == "ineligible"
    assert result.mutual_score is None
    assert result.directional_a_to_b is None
