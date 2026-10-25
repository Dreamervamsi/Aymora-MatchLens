import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    DimensionWeights,
)
from matchlens.engine.ranker import rank_candidates


def test_ranking_top_k_filtering_and_sorting():
    # User A seeking long-term partner
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(
            age=28, gender="man", relationship_intent="long_term",
            core_values=["honesty", "family"], interests=["hiking", "reading"]
        ),
        expectations=PartnerPreferences(
            min_age=22, max_age=32, acceptable_genders=["woman"],
            desired_intentions=["long_term"], desired_values=["honesty", "family"]
        ),
        weights=DimensionWeights(
            core_values=0.40, relationship_intentions=0.30,
            lifestyle_compatibility=0.10, communication_preferences=0.10, shared_interests=0.10
        ),
    )

    # Candidate 1: Perfect match
    cand_1 = UserProfile(
        user_id="cand_1",
        attributes=UserAttributes(
            age=26, gender="woman", relationship_intent="long_term",
            core_values=["honesty", "family"], interests=["hiking", "reading"]
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["man"],
            desired_intentions=["long_term"], desired_values=["honesty", "family"]
        ),
    )

    # Candidate 2: Partial match
    cand_2 = UserProfile(
        user_id="cand_2",
        attributes=UserAttributes(
            age=27, gender="woman", relationship_intent="long_term",
            core_values=["honesty"], interests=["hiking"]
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["man"],
            desired_intentions=["long_term"], desired_values=["honesty"]
        ),
    )

    # Candidate 3: Ineligible (age out of range)
    cand_3 = UserProfile(
        user_id="cand_3",
        attributes=UserAttributes(
            age=45, gender="woman", relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["man"],
        ),
    )

    top_matches, meta = rank_candidates(
        requesting_user=user_a,
        candidates=[cand_1, cand_2, cand_3],
        top_k=2,
        min_evidence_coverage=0.0,  # Include all eligible candidates
    )

    assert meta.total_candidates == 3
    assert meta.eligible_candidates == 2
    assert meta.returned_count == 2

    # cand_1 should rank higher than cand_2
    assert top_matches[0].user_b_id == "cand_1"
    assert top_matches[1].user_b_id == "cand_2"
    assert top_matches[0].mutual_score > top_matches[1].mutual_score


def test_deterministic_tie_breaking():
    user_a = UserProfile(
        user_id="user_a",
        attributes=UserAttributes(
            age=28, gender="man", relationship_intent="long_term",
            core_values=["honesty"]
        ),
        expectations=PartnerPreferences(
            min_age=22, max_age=32, acceptable_genders=["woman"],
            desired_intentions=["long_term"], desired_values=["honesty"]
        ),
    )

    # Two identical candidates with different IDs ('cand_z' and 'cand_a')
    cand_z = UserProfile(
        user_id="cand_z",
        attributes=UserAttributes(
            age=26, gender="woman", relationship_intent="long_term", core_values=["honesty"]
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["man"],
            desired_intentions=["long_term"], desired_values=["honesty"]
        ),
    )

    cand_a = UserProfile(
        user_id="cand_a",
        attributes=UserAttributes(
            age=26, gender="woman", relationship_intent="long_term", core_values=["honesty"]
        ),
        expectations=PartnerPreferences(
            min_age=25, max_age=35, acceptable_genders=["man"],
            desired_intentions=["long_term"], desired_values=["honesty"]
        ),
    )

    top_matches, meta = rank_candidates(
        requesting_user=user_a,
        candidates=[cand_z, cand_a],
        top_k=2,
        min_evidence_coverage=0.0,
    )

    # With identical scores, alphabetical sorting puts 'cand_a' before 'cand_z'
    assert top_matches[0].user_b_id == "cand_a"
    assert top_matches[1].user_b_id == "cand_z"
