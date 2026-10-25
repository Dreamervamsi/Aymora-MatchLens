import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.dimension_scorers import (
    score_core_values,
    score_relationship_intentions,
    score_lifestyle,
    score_communication,
    score_shared_interests,
)


def test_core_values_scoring():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(desired_values=["honesty", "family", "ambition"]),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(core_values=["honesty", "family", "creativity"]),
    )

    score, shared, gaps, evidence = score_core_values(evaluator, candidate)
    assert score == pytest.approx(66.67, 0.1)
    assert len(shared) == 2  # honesty, family
    assert len(gaps) == 1  # ambition missing


def test_relationship_intentions_scoring():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(desired_intentions=["long_term", "marriage"]),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(relationship_intent="long_term"),
    )

    score, shared, gaps, _ = score_relationship_intentions(evaluator, candidate)
    assert score == 100.0
    assert len(shared) == 1
    assert len(gaps) == 0


def test_shared_interests_jaccard_scoring():
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(interests=["hiking", "reading", "cooking"]),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(interests=["reading", "cooking", "gaming"]),
    )

    score, shared, gaps, _ = score_shared_interests(evaluator, candidate)
    # Jaccard: 2 shared / 4 total unique = 50.0%
    assert score == 50.0
    assert len(shared) == 2


def test_communication_with_scenarios():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(desired_communication_styles=["direct"]),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference="cool_down_first",
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(communication_style="direct"),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    assert score == 100.0
    assert len(scenario_ev) == 1
    assert "aligns with expectation" in scenario_ev[0]


def test_missing_data_returns_none():
    evaluator = UserProfile(user_id="e1")  # Default empty preferences
    candidate = UserProfile(user_id="c1")

    score, _, _, _ = score_core_values(evaluator, candidate)
    assert score is None
