import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    DimensionWeights,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.directional import calculate_directional_score


def test_calculate_directional_score_complete_profile():
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(interests=["hiking", "reading"]),
        expectations=PartnerPreferences(
            desired_values=["honesty"],
            desired_intentions=["long_term"],
            acceptable_smoking=["never"],
            desired_communication_styles=["direct"],
        ),
        weights=DimensionWeights(
            core_values=0.30,
            relationship_intentions=0.25,
            lifestyle_compatibility=0.20,
            communication_preferences=0.15,
            shared_interests=0.10,
        ),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(
            core_values=["honesty"],
            relationship_intent="long_term",
            smoking="never",
            communication_style="direct",
            interests=["hiking", "reading"],
        ),
    )

    directional = calculate_directional_score(evaluator, candidate)
    assert directional.evaluator_id == "e1"
    assert directional.candidate_id == "c1"
    assert directional.directional_score == 100.0
    assert directional.evidence_coverage == 100.0
    assert len(directional.dimension_scores) == 5


def test_asymmetric_weights_and_partial_data():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(
            desired_values=["honesty", "family"],  # core values
            desired_intentions=["long_term"],      # intentions
        ),
        weights=DimensionWeights(
            core_values=0.50,
            relationship_intentions=0.50,
            lifestyle_compatibility=0.0,
            communication_preferences=0.0,
            shared_interests=0.0,
        ),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(
            core_values=["honesty"],  # 1 of 2 matched -> 50%
            relationship_intent="long_term",  # 100%
        ),
    )

    directional = calculate_directional_score(evaluator, candidate)
    # Total active weight = 0.50 + 0.50 = 1.00
    # Score = (50 * 0.5 + 100 * 0.5) / 1.00 = 75.0
    assert directional.directional_score == 75.0
    assert directional.evidence_coverage == 100.0


def test_missing_dimension_data_handling():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(
            desired_values=["honesty"],  # core_values present
        ),
        weights=DimensionWeights(
            core_values=0.50,
            relationship_intentions=0.50,
            lifestyle_compatibility=0.0,
            communication_preferences=0.0,
            shared_interests=0.0,
        ),
    )
    # Candidate lacks relationship_intent, so relationship_intentions has no sufficient data
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(core_values=["honesty"]),
    )

    directional = calculate_directional_score(evaluator, candidate)
    # Only core_values (weight 0.50) has data
    # Active weight = 0.50 out of total 1.00 -> coverage = 50%
    assert directional.evidence_coverage == 50.0
    assert directional.directional_score == 100.0
    assert directional.dimension_scores["core_values"].has_sufficient_data is True
    assert directional.dimension_scores["relationship_intentions"].has_sufficient_data is False
    assert directional.dimension_scores["relationship_intentions"].score is None
