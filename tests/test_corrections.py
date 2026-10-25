import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    Dealbreakers,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.eligibility import check_mutual_eligibility
from matchlens.engine.dimension_scorers import (
    score_core_values,
    score_lifestyle,
    score_communication,
    score_shared_interests,
    _blend_dimension_scores,
)


def test_missing_mandatory_info_pending_status():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(desired_intentions=["long_term"]),
        dealbreakers=Dealbreakers(strict_intention_match=True),
    )
    # user_b has missing relationship_intent (None)
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(age=26, gender="woman", relationship_intent=None),
        expectations=PartnerPreferences(desired_intentions=["long_term"]),
        dealbreakers=Dealbreakers(strict_intention_match=True),
    )

    status, reasons = check_mutual_eligibility(user_a, user_b)
    assert status == "pending_information"
    assert any("Candidate's relationship intent is unknown/missing" in r for r in reasons)


def test_self_matching_disallowed():
    user_a = UserProfile(user_id="user_a")
    status, reasons = check_mutual_eligibility(user_a, user_a)
    assert status == "ineligible"
    assert any("Self-matching is disallowed" in r for r in reasons)


def test_no_implicit_scenario_expectation_assumption():
    # Evaluator has scenario response with NO expected_partner_preference set
    evaluator = UserProfile(
        user_id="e1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference=None,  # No explicit partner expectation
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    # Since no expected_partner_preference was provided, scenario comparison cannot be made
    assert score is None
    assert len(scenario_ev) == 0


def test_explicit_partner_expectation_scenario_scoring():
    evaluator = UserProfile(
        user_id="e1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference="discuss_immediately",  # Explicit expectation
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="discuss_immediately",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    assert score == 100.0
    assert len(scenario_ev) == 1
    assert "ALIGNS" in scenario_ev[0]


def test_scenario_only_scoring():
    # Profile with no communication attributes, only scenario
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference="discuss_immediately",
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(),
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="discuss_immediately",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    assert score == 100.0  # Uses scenario score without falling back to 50.0


def test_zero_importance_scenario_ignored():
    evaluator = UserProfile(
        user_id="e1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference="discuss_immediately",
                importance=0.0,  # Zero importance
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="discuss_immediately",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    assert score is None
    assert len(scenario_ev) == 0


def test_mismatched_scenario_definitions_ignored():
    evaluator = UserProfile(
        user_id="e1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="communication_preferences",
                normalized_preference="cool_down_first",
                expected_partner_preference="discuss_immediately",
            )
        ],
    )
    candidate = UserProfile(
        user_id="c1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_01",
                target_dimension="lifestyle_compatibility",  # Mismatched target dimension
                normalized_preference="discuss_immediately",
            )
        ],
    )

    score, shared, gaps, scenario_ev = score_communication(evaluator, candidate)
    assert score is None
    assert len(scenario_ev) == 0


def test_consistent_string_normalization():
    evaluator = UserProfile(
        user_id="e1",
        expectations=PartnerPreferences(desired_values=["  HONESTY  ", "Family"]),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(core_values=["honesty", "FAMILY "]),
    )

    score, shared, gaps, _ = score_core_values(evaluator, candidate)
    assert score == 100.0
    assert len(shared) == 2
