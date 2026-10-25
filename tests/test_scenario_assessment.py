import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from matchlens.ai.scenario_extractor import GroqScenarioExtractor, ScenarioInterpretationResult
from matchlens.assessment.integration import attach_scenario_responses
from matchlens.assessment.models import (
    AssessmentProgress,
    AssessmentStage,
    AssessmentState,
    AssessmentStatus,
)
from matchlens.assessment.orchestrator import ScenarioAssessmentOrchestrator
from matchlens.assessment.state_manager import AssessmentStateManager
from matchlens.engine.reciprocal import calculate_reciprocal_match
from matchlens.models.profile import PartnerPreferences, UserAttributes, UserProfile
from matchlens.models.scenario import ScenarioCatalog, ScenarioResponse


@pytest.fixture
def assessment_orchestrator():
    extractor = GroqScenarioExtractor(client=None)  # AI client None for non-AI direct tests
    state_manager = AssessmentStateManager()
    return ScenarioAssessmentOrchestrator(state_manager=state_manager, extractor=extractor)


@pytest.fixture
def sample_profile_a():
    return UserProfile(
        user_id="user_a",
        attributes=UserAttributes(
            age=28,
            gender="woman",
            relationship_intent="long_term",
            core_values=["family", "honesty"],
            communication_style="direct",
            conflict_resolution="discuss_immediately",
        ),
        expectations=PartnerPreferences(
            min_age=25,
            max_age=35,
            acceptable_genders=["man"],
            desired_intentions=["long_term"],
            desired_values=["honesty"],
            desired_conflict_resolutions=["discuss_immediately", "cool_down_first"],
        ),
    )


@pytest.fixture
def sample_profile_b():
    return UserProfile(
        user_id="user_b",
        attributes=UserAttributes(
            age=30,
            gender="man",
            relationship_intent="long_term",
            core_values=["honesty", "family"],
            communication_style="direct",
            conflict_resolution="cool_down_first",
        ),
        expectations=PartnerPreferences(
            min_age=24,
            max_age=32,
            acceptable_genders=["woman"],
            desired_intentions=["long_term"],
            desired_values=["family"],
            desired_conflict_resolutions=["discuss_immediately"],
        ),
    )


# Test 1: Assessment creation and scenario ordering
def test_1_assessment_creation_and_ordering(assessment_orchestrator):
    selected = ["conflict_resolution_01", "social_energy_01"]
    res = assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=selected)

    assert res.assessment_id is not None
    assert res.status == AssessmentStatus.ACTIVE
    assert res.current_stage == AssessmentStage.SELF_BEHAVIOR
    assert res.current_scenario_id == "conflict_resolution_01"
    assert res.progress.total_scenarios == 2
    assert res.progress.current_scenario_index == 0


# Test 2: Self-response collection
@pytest.mark.anyio
async def test_2_self_response_collection(assessment_orchestrator):
    start_res = assessment_orchestrator.start_assessment(user_id="u1")
    aid = start_res.assessment_id

    turn1 = await assessment_orchestrator.submit_response(aid, "discuss_immediately")

    assert turn1.status == AssessmentStatus.ACTIVE
    assert turn1.current_stage == AssessmentStage.PARTNER_EXPECTATION
    assert turn1.current_scenario_id == "conflict_resolution_01"

    state = assessment_orchestrator.get_assessment_state(aid)
    draft = state.collected_responses["conflict_resolution_01"]
    assert draft.self_response == "discuss_immediately"
    assert draft.partner_expectation is None


# Test 3: Partner-expectation collection
@pytest.mark.anyio
async def test_3_partner_expectation_collection(assessment_orchestrator):
    start_res = assessment_orchestrator.start_assessment(user_id="u1")
    aid = start_res.assessment_id

    await assessment_orchestrator.submit_response(aid, "discuss_immediately")
    turn2 = await assessment_orchestrator.submit_response(aid, "cool_down_first")

    assert turn2.status == AssessmentStatus.ACTIVE
    assert turn2.current_stage == AssessmentStage.SELF_BEHAVIOR
    assert turn2.current_scenario_id == "social_energy_01"

    state = assessment_orchestrator.get_assessment_state(aid)
    draft = state.collected_responses["conflict_resolution_01"]
    assert draft.self_response == "discuss_immediately"
    assert draft.partner_expectation == "cool_down_first"


# Test 4: Distinct self and partner responses
@pytest.mark.anyio
async def test_4_distinct_self_and_partner_responses(assessment_orchestrator):
    start_res = assessment_orchestrator.start_assessment(user_id="u1")
    aid = start_res.assessment_id

    # Self: cool_down_first | Partner: discuss_immediately
    await assessment_orchestrator.submit_response(aid, "cool_down_first")
    await assessment_orchestrator.submit_response(aid, "discuss_immediately")

    state = assessment_orchestrator.get_assessment_state(aid)
    draft = state.collected_responses["conflict_resolution_01"]
    assert draft.self_response == "cool_down_first"
    assert draft.partner_expectation == "discuss_immediately"
    assert draft.self_response != draft.partner_expectation


# Test 5: Invalid options and unknown scenario IDs
@pytest.mark.anyio
async def test_5_invalid_options_and_unknown_scenarios(assessment_orchestrator):
    with pytest.raises(ValueError, match="Unknown scenario ID 'unknown_scen_999'"):
        assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=["unknown_scen_999"])

    start_res = assessment_orchestrator.start_assessment(user_id="u1")
    aid = start_res.assessment_id

    # Submitting an invalid option should prompt for clarification/re-entry without crashing state
    turn = await assessment_orchestrator.submit_response(aid, "invalid_option_xyz")
    assert turn.unresolved_clarification is not None or "invalid" in turn.prompt_text.lower() or "couldn't" in turn.prompt_text.lower()


# Test 6: Free-text normalization with mocked Groq
@pytest.mark.anyio
async def test_6_freetext_normalization_mocked_groq():
    mock_extractor = GroqScenarioExtractor(client=None)
    mock_extractor.normalize_response = AsyncMock(
        return_value=ScenarioInterpretationResult(
            matched_option="cool_down_first",
            confidence=0.92,
            is_ambiguous=False,
            reasoning="User stated they prefer to take a walk to calm down before talking.",
        )
    )

    orch = ScenarioAssessmentOrchestrator(extractor=mock_extractor)
    res = orch.start_assessment(user_id="u1")

    turn1 = await orch.submit_response(res.assessment_id, "I usually go for a walk alone to calm down first.")
    assert turn1.current_stage == AssessmentStage.PARTNER_EXPECTATION

    state = orch.get_assessment_state(res.assessment_id)
    assert state.collected_responses["conflict_resolution_01"].self_response == "cool_down_first"


# Test 7: Ambiguous AI interpretations
@pytest.mark.anyio
async def test_7_ambiguous_ai_interpretation_flow():
    mock_extractor = GroqScenarioExtractor(client=None)
    mock_extractor.normalize_response = AsyncMock(
        return_value=ScenarioInterpretationResult(
            matched_option="discuss_immediately",
            confidence=0.55,
            is_ambiguous=True,
            reasoning="User expressed hesitation.",
            clarification_prompt="Did you mean discuss immediately or written first?",
        )
    )

    orch = ScenarioAssessmentOrchestrator(extractor=mock_extractor)
    res = orch.start_assessment(user_id="u1")

    # Turn 1: natural language yielding ambiguous interpretation
    turn1 = await orch.submit_response(res.assessment_id, "I kind of like talking right away maybe?")
    assert turn1.unresolved_clarification is not None
    assert "discuss immediately" in turn1.prompt_text.lower()

    # Turn 2: User clarifies explicitly with "discuss_immediately"
    turn2 = await orch.submit_response(res.assessment_id, "discuss_immediately")
    assert turn2.unresolved_clarification is None
    assert turn2.current_stage == AssessmentStage.PARTNER_EXPECTATION


# Test 8: AI failure fallback
@pytest.mark.anyio
async def test_8_ai_failure_fallback():
    mock_extractor = GroqScenarioExtractor(client=None)
    mock_extractor.normalize_response = AsyncMock(side_effect=RuntimeError("Groq API Timeout"))

    orch = ScenarioAssessmentOrchestrator(extractor=mock_extractor)
    res = orch.start_assessment(user_id="u1")

    # Direct option input should still succeed without invoking AI
    turn1 = await orch.submit_response(res.assessment_id, "cool_down_first")
    assert turn1.current_stage == AssessmentStage.PARTNER_EXPECTATION


# Test 9: Assessment progress and completion
@pytest.mark.anyio
async def test_9_assessment_progress_and_completion(assessment_orchestrator):
    selected = ["conflict_resolution_01"]
    res = assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=selected)
    aid = res.assessment_id

    assert res.progress.percentage == 0.0

    await assessment_orchestrator.submit_response(aid, "discuss_immediately")
    state = assessment_orchestrator.get_assessment_state(aid)
    assert state.progress.percentage == 50.0

    turn_review = await assessment_orchestrator.submit_response(aid, "cool_down_first")
    assert turn_review.status == AssessmentStatus.READY_FOR_REVIEW
    assert turn_review.progress.percentage == 100.0


# Test 10: Independent corrections during review
@pytest.mark.anyio
async def test_10_independent_corrections_during_review(assessment_orchestrator):
    selected = ["conflict_resolution_01"]
    res = assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=selected)
    aid = res.assessment_id

    await assessment_orchestrator.submit_response(aid, "discuss_immediately")
    await assessment_orchestrator.submit_response(aid, "cool_down_first")

    state = assessment_orchestrator.get_assessment_state(aid)
    assert state.status == AssessmentStatus.READY_FOR_REVIEW

    # Correct partner expectation independently
    turn_corr = assessment_orchestrator.correct_response(
        assessment_id=aid,
        scenario_id="conflict_resolution_01",
        target="partner_expectation",
        new_value="written_first",
    )

    state_after = assessment_orchestrator.get_assessment_state(aid)
    draft = state_after.collected_responses["conflict_resolution_01"]
    assert draft.self_response == "discuss_immediately"  # unchanged
    assert draft.partner_expectation == "written_first"  # updated


# Test 11: Explicit assessment confirmation
@pytest.mark.anyio
async def test_11_explicit_assessment_confirmation(assessment_orchestrator):
    selected = ["conflict_resolution_01"]
    res = assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=selected)
    aid = res.assessment_id

    await assessment_orchestrator.submit_response(aid, "discuss_immediately")
    await assessment_orchestrator.submit_response(aid, "cool_down_first")

    turn_final = assessment_orchestrator.confirm_assessment(aid)
    assert turn_final.status == AssessmentStatus.COMPLETED
    assert turn_final.current_stage == AssessmentStage.COMPLETED

    canonical_resps = assessment_orchestrator.get_completed_responses(aid)
    assert len(canonical_resps) == 1
    scen = canonical_resps[0]
    assert scen.scenario_id == "conflict_resolution_01"
    assert scen.normalized_preference == "discuss_immediately"
    assert scen.expected_partner_preference == "cool_down_first"


# Test 12: ScenarioResponse compatibility with reciprocal matching engine
@pytest.mark.anyio
async def test_12_matching_engine_compatibility(sample_profile_a, sample_profile_b):
    scen_a = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="discuss_immediately",
        expected_partner_preference="cool_down_first",
    )
    scen_b = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="cool_down_first",
        expected_partner_preference="discuss_immediately",
    )

    profile_a = attach_scenario_responses(sample_profile_a, [scen_a])
    profile_b = attach_scenario_responses(sample_profile_b, [scen_b])

    match_result = calculate_reciprocal_match(profile_a, profile_b)

    assert match_result.is_eligible is True
    assert match_result.mutual_score is not None
    assert match_result.mutual_score > 0.0

    # Verify scenario evidence is present in communication score
    comm_a_b = match_result.directional_a_to_b.dimension_scores["communication_preferences"]
    assert len(comm_a_b.scenario_evidence) > 0
    assert "ALIGNS" in comm_a_b.scenario_evidence[0]


# Test 13: Profile integration without mutating original data
def test_13_profile_integration_non_mutating(sample_profile_a):
    scen = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="discuss_immediately",
        expected_partner_preference="cool_down_first",
    )

    original_scen_count = len(sample_profile_a.scenarios)
    updated_profile = attach_scenario_responses(sample_profile_a, [scen])

    assert len(sample_profile_a.scenarios) == original_scen_count
    assert len(updated_profile.scenarios) == original_scen_count + 1
    assert updated_profile.user_id == sample_profile_a.user_id


# Test 14: Duplicate scenario handling
def test_14_duplicate_scenario_handling(sample_profile_a):
    scen1 = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="discuss_immediately",
        expected_partner_preference="cool_down_first",
    )
    scen2 = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="cool_down_first",
        expected_partner_preference="discuss_immediately",
    )

    profile_with_scen = attach_scenario_responses(sample_profile_a, [scen1])

    # Should raise error if replace_existing is False
    with pytest.raises(ValueError, match="Duplicate scenario_id"):
        attach_scenario_responses(profile_with_scen, [scen2], replace_existing=False)

    # Should succeed and overwrite when replace_existing is True
    replaced_profile = attach_scenario_responses(profile_with_scen, [scen2], replace_existing=True)
    assert len(replaced_profile.scenarios) == 1
    assert replaced_profile.scenarios[0].normalized_preference == "cool_down_first"


# Test 15: State serialization and restoration
@pytest.mark.anyio
async def test_15_state_serialization_and_restoration(assessment_orchestrator):
    selected = ["conflict_resolution_01", "social_energy_01"]
    start_res = assessment_orchestrator.start_assessment(user_id="u1", selected_scenario_ids=selected)
    aid = start_res.assessment_id

    await assessment_orchestrator.submit_response(aid, "discuss_immediately")

    sm = assessment_orchestrator.state_manager
    serialized_json = sm.serialize_state(aid)

    # Clear in-memory state store and restore
    sm._sessions.clear()
    assert sm.get_session(aid) is None

    restored_state = sm.deserialize_state(serialized_json)
    assert restored_state.assessment_id == aid
    assert restored_state.current_stage == AssessmentStage.PARTNER_EXPECTATION
    assert restored_state.collected_responses["conflict_resolution_01"].self_response == "discuss_immediately"
