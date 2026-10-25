import pytest
from matchlens.models.profile import (
    UserProfile,
    UserAttributes,
    PartnerPreferences,
    DimensionWeights,
)
from matchlens.models.scenario import ScenarioResponse, ScenarioCatalog, ScenarioDefinition
from matchlens.engine.directional import calculate_directional_score
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.config import DEFAULT_MIN_EVIDENCE_COVERAGE


def test_no_duplicate_scoring_models():
    from matchlens.models import scoring
    # Confirm single canonical definition in module namespace
    assert hasattr(scoring, "MatchResult")
    assert hasattr(scoring, "EvidenceRecord")
    assert hasattr(scoring, "DirectionalScore")


def test_scenario_catalog_validation():
    # Known scenario definition validation
    defn = ScenarioCatalog.get_definition("conflict_resolution_01")
    assert defn is not None
    assert defn.target_dimension == "communication_preferences"
    assert "cool_down_first" in defn.allowed_options


def test_unrestricted_vs_missing_preference():
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(age=30, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(
            desired_values=["any"],  # Unrestricted preference
            desired_intentions=["long_term"],
            min_age=20,
            max_age=40,
            acceptable_genders=["woman"],
        ),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(
            age=28,
            gender="woman",
            core_values=["creativity", "art"],
            relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=25,
            max_age=35,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
        ),
    )

    directional = calculate_directional_score(evaluator, candidate)
    assert directional.dimension_scores["core_values"].has_sufficient_data is True
    assert directional.dimension_scores["core_values"].score == 100.0


def test_low_coverage_flagging():
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(
            desired_values=["honesty"],  # Only 1 dimension populated
            min_age=20,
            max_age=40,
            acceptable_genders=["woman"],
            desired_intentions=["long_term"],
        ),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(
            age=26,
            gender="woman",
            core_values=["honesty"],
            relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=20,
            max_age=40,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
        ),
    )

    result = calculate_reciprocal_match(evaluator, candidate, min_evidence_coverage=60.0)
    assert result.is_eligible is True
    assert result.evidence_coverage < 60.0
    assert result.is_low_coverage is True


def test_structured_evidence_records_generated():
    evaluator = UserProfile(
        user_id="e1",
        attributes=UserAttributes(age=28, gender="man", relationship_intent="long_term"),
        expectations=PartnerPreferences(
            desired_values=["honesty"],
            desired_intentions=["long_term"],
            min_age=20,
            max_age=40,
            acceptable_genders=["woman"],
        ),
    )
    candidate = UserProfile(
        user_id="c1",
        attributes=UserAttributes(
            age=26,
            gender="woman",
            core_values=["honesty"],
            relationship_intent="long_term",
        ),
        expectations=PartnerPreferences(
            min_age=20,
            max_age=40,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
        ),
    )

    result = calculate_reciprocal_match(evaluator, candidate)
    assert result.evidence_summary is not None
    assert len(result.evidence_summary.structured_evidence) > 0

    record = result.evidence_summary.structured_evidence[0]
    assert hasattr(record, "source_type")
    assert hasattr(record, "outcome")
    assert hasattr(record, "score_impact")
