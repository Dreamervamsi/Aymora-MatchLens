import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    Dealbreakers,
)
from matchlens.models.scenario import ScenarioResponse
from matchlens.engine.dimension_scorers import score_communication
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.engine.ranker import rank_candidates, RankingMetaData


def test_invalid_scenario_choice_catalog_validation():
    # Attempting an option not in KNOWN_SCENARIO_CATALOG allowed options should raise ValidationError
    with pytest.raises(Exception):
        ScenarioResponse(
            scenario_id="conflict_resolution_01",
            target_dimension="communication_preferences",
            normalized_preference="invalid_choice_option_abc",
        )


def test_invalid_expected_partner_preference_catalog_validation():
    with pytest.raises(Exception):
        ScenarioResponse(
            scenario_id="conflict_resolution_01",
            target_dimension="communication_preferences",
            normalized_preference="cool_down_first",
            expected_partner_preference="invalid_choice_option_xyz",
        )


def test_candidate_partner_expectation_only_perspective_not_used_as_self_behavior():
    evaluator = UserProfile(
        user_id="e1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_resolution_01",
                target_dimension="communication_preferences",
                perspective="self_behavior",
                normalized_preference="cool_down_first",
                expected_partner_preference="discuss_immediately",
            )
        ],
    )
    # Candidate scenario response has perspective="partner_expectation"
    # This describes candidate's wish for a partner, NOT candidate's self behavior
    candidate = UserProfile(
        user_id="c1",
        scenarios=[
            ScenarioResponse(
                scenario_id="conflict_resolution_01",
                target_dimension="communication_preferences",
                perspective="partner_expectation",  # NOT self_behavior
                normalized_preference="discuss_immediately",
            )
        ],
    )

    score, shared, gaps, scenario_ev, records = score_communication(evaluator, candidate)
    # Since candidate response is partner_expectation, it cannot be used as candidate self behavior
    assert score is None
    assert len(scenario_ev) == 0


def test_asymmetric_coverage_safeguard():
    # User A has complete profile -> A->B coverage = 100%
    # User B has sparse profile -> B->A coverage = 20%
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(
            age=28, gender="man", relationship_intent="long_term",
            core_values=["honesty"], interests=["reading"]
        ),
        expectations=PartnerPreferences(
            min_age=20, max_age=40, acceptable_genders=["woman"],
            desired_intentions=["long_term"], desired_values=["honesty"]
        ),
    )
    user_b = UserProfile(
        user_id="user_b",
        attributes=UserAttributes(
            age=26, gender="woman", relationship_intent="long_term"
        ),
        expectations=PartnerPreferences(
            min_age=20, max_age=40, acceptable_genders=["man"],
            desired_intentions=["long_term"],
            # Lacks desired_values, communication, lifestyle, interests -> low coverage for B->A
        ),
    )

    result = calculate_reciprocal_match(user_a, user_b, min_evidence_coverage=60.0)
    assert result.is_eligible is True
    # Average coverage might be ~60%, but since B->A is low (<60%), pair is flagged as low coverage
    assert result.is_low_coverage is True


def test_ranking_input_validation():
    user = UserProfile(user_id="u1")
    cand = UserProfile(user_id="c1")

    with pytest.raises(ValueError):
        rank_candidates(requesting_user=user, candidates=[cand], top_k=0)

    with pytest.raises(ValueError):
        rank_candidates(requesting_user=user, candidates=[cand], top_k=-5)

    with pytest.raises(ValueError):
        rank_candidates(requesting_user=user, candidates=[cand], min_evidence_coverage=150.0)


def test_duplicate_candidate_ids_deduplication():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(min_age=20, max_age=40, acceptable_genders=["woman"], desired_intentions=["long_term"]),
    )
    cand_dup1 = UserProfile(
        user_id="cand_1",
        attributes=UserAttributes(age=26, gender="woman", relationship_intent="long_term"),
        expectations=PartnerPreferences(min_age=20, max_age=40, acceptable_genders=["man"], desired_intentions=["long_term"]),
    )
    cand_dup2 = UserProfile(
        user_id="cand_1",  # Duplicate ID
        attributes=UserAttributes(age=26, gender="woman", relationship_intent="long_term"),
        expectations=PartnerPreferences(min_age=20, max_age=40, acceptable_genders=["man"], desired_intentions=["long_term"]),
    )

    top_matches, meta = rank_candidates(
        requesting_user=user_a,
        candidates=[cand_dup1, cand_dup2],
        top_k=5,
        min_evidence_coverage=0.0,
    )

    assert meta.total_candidates == 1  # Deduplicated from 2 to 1
    assert len(top_matches) == 1
    assert top_matches[0].user_b_id == "cand_1"


def test_pending_information_ranking_metadata():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(desired_intentions=["long_term"]),
        dealbreakers=Dealbreakers(strict_intention_match=True),
    )
    # Candidate lacks relationship_intent (None) -> pending_information
    cand_pending = UserProfile(
        user_id="cand_p",
        attributes=UserAttributes(age=26, gender="woman", relationship_intent=None),
        expectations=PartnerPreferences(desired_intentions=["long_term"]),
        dealbreakers=Dealbreakers(strict_intention_match=True),
    )

    top_matches, meta = rank_candidates(
        requesting_user=user_a,
        candidates=[cand_pending],
        top_k=3,
        min_evidence_coverage=0.0,
    )

    assert meta.pending_information_candidates == 1
    assert meta.returned_count == 0
