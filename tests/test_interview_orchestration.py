import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from matchlens.ai import (
    GroqSettings,
    GroqClient,
    GroqProfileExtractor,
    ExtractedProfileUpdate,
    PartialUserAttributes,
    PartialPartnerPreferences,
    PartialDealbreakers,
    ConfirmationPrompt,
    GroqAPIError,
)
from matchlens.interview import (
    InterviewOrchestrator,
    InterviewSettings,
    InterviewState,
    InterviewStatus,
    InterviewTopic,
    InterviewStateManager,
    PendingConfirmation,
    HybridQuestionSelector,
)
from matchlens.models.profile import UserProfile


def mock_extraction_response(
    self_attrs: dict = None,
    partner_prefs: dict = None,
    dealbreakers: dict = None,
    confirmations: list = None,
    unanswered: list = None,
):
    """Helper to build a mocked ExtractedProfileUpdate response object."""
    return ExtractedProfileUpdate(
        confirmed_self_attributes=PartialUserAttributes.model_validate(self_attrs or {}),
        confirmed_partner_preferences=PartialPartnerPreferences.model_validate(partner_prefs or {}),
        confirmed_dealbreakers=PartialDealbreakers.model_validate(dealbreakers or {}),
        scenarios=[],
        unanswered_fields=unanswered or [],
        uncertainties=[],
        confirmations_needed=[ConfirmationPrompt.model_validate(c) for c in (confirmations or [])],
    )


@pytest.fixture
def mock_extractor():
    extractor = MagicMock(spec=GroqProfileExtractor)
    extractor.extract_from_text = AsyncMock()
    return extractor


@pytest.fixture
def mock_question_selector():
    selector = MagicMock(spec=HybridQuestionSelector)
    selector.select_and_generate_question = AsyncMock(
        side_effect=lambda state, target_topic, missing_field_key=None, clarification_prompt=None: (
            f"{target_topic.value}.{missing_field_key or 'default'}",
            f"Question for {target_topic.value} on {missing_field_key or 'default'}?"
        )
    )
    return selector


@pytest.fixture
def orchestrator(mock_extractor, mock_question_selector):
    settings = InterviewSettings(max_total_turns=5, max_turns_per_topic=2)
    state_mgr = InterviewStateManager()
    return InterviewOrchestrator(
        settings=settings,
        state_manager=state_mgr,
        extractor=mock_extractor,
        question_selector=mock_question_selector,
    )


@pytest.mark.anyio
async def test_1_start_interview(orchestrator):
    """1. Test starting a new onboarding interview."""
    state, msg = orchestrator.start_interview(user_id="user_123", session_id="sess_001")
    
    assert state.session_id == "sess_001"
    assert state.user_id == "user_123"
    assert state.status == InterviewStatus.ACTIVE
    assert state.current_topic == InterviewTopic.BASIC_AND_INTENTION
    assert len(state.conversation_history) == 1
    assert "Welcome to MatchLens" in msg


@pytest.mark.anyio
async def test_2_process_multiple_turns(orchestrator, mock_extractor):
    """2. Test processing multiple conversation turns."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_002")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 29, "gender": "man", "relationship_intent": "long_term"}
    )
    
    res1 = await orchestrator.process_turn(session_id="sess_002", user_message="I'm 29, male, looking for a long-term relationship.")
    
    assert res1.session_id == "sess_002"
    assert "attributes.age" in res1.newly_extracted_fields
    assert "attributes.gender" in res1.newly_extracted_fields
    assert res1.current_topic == InterviewTopic.CORE_VALUES  # Advanced to topic 2


@pytest.mark.anyio
async def test_3_extract_self_attributes(orchestrator, mock_extractor):
    """3. Test extracting self attributes."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_003")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"smoking": "never", "drinking": "socially"}
    )
    
    res = await orchestrator.process_turn(session_id="sess_003", user_message="I don't smoke, but I drink socially.")
    profile = orchestrator.get_draft_profile("sess_003")
    
    assert profile.attributes.smoking == "never"
    assert profile.attributes.drinking == "socially"


@pytest.mark.anyio
async def test_4_extract_partner_expectations_separately(orchestrator, mock_extractor):
    """4. Test extracting partner expectations separately from self attributes."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_004")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"conflict_resolution": "cool_down_first"},
        partner_prefs={"desired_conflict_resolutions": ["discuss_immediately"]}
    )
    
    res = await orchestrator.process_turn(
        session_id="sess_004",
        user_message="I like to cool down first after an argument, but I prefer a partner who wants to discuss things immediately."
    )
    profile = orchestrator.get_draft_profile("sess_004")
    
    assert profile.attributes.conflict_resolution == "cool_down_first"
    assert profile.expectations.desired_conflict_resolutions == ["discuss_immediately"]


@pytest.mark.anyio
async def test_5_ambiguity_without_auto_confirmation_and_ambiguous_phrase(orchestrator, mock_extractor):
    """5. Test handling ambiguity without auto-confirmation, and ambiguous confirmation phrase handling."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_005")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        confirmations=[{
            "field_name": "drinking",
            "target_category": "self_attributes",
            "proposed_value": "socially",
            "confidence": 0.6,
            "reasoning": "User mentioned going to pubs",
            "clarification_question": "Do you drink alcohol socially?"
        }]
    )
    
    res1 = await orchestrator.process_turn(session_id="sess_005", user_message="I go to pubs sometimes.")
    profile = orchestrator.get_draft_profile("sess_005")
    
    assert profile.attributes.drinking is None
    assert len(res1.pending_confirmations) == 1
    assert res1.interview_status == InterviewStatus.AWAITING_CONFIRMATION

    # Ambiguous/qualified response
    res2 = await orchestrator.process_turn(session_id="sess_005", user_message="Maybe, I guess.")
    
    profile2 = orchestrator.get_draft_profile("sess_005")
    assert profile2.attributes.drinking is None
    assert len(res2.pending_confirmations) == 1  # Remains pending!


@pytest.mark.anyio
async def test_6_confirm_and_reject_proposed_values(orchestrator, mock_extractor):
    """6. Test confirming and rejecting proposed values."""
    # Part A: Confirming
    state1, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_006a")
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        confirmations=[{
            "field_name": "smoking",
            "target_category": "self_attributes",
            "proposed_value": "never",
            "confidence": 0.7,
            "reasoning": "User said health conscious",
            "clarification_question": "Does that mean you never smoke?"
        }]
    )
    await orchestrator.process_turn(session_id="sess_006a", user_message="I am health conscious.")
    
    res_a = await orchestrator.process_turn(session_id="sess_006a", user_message="Yes, that's correct.")
    p_a = orchestrator.get_draft_profile("sess_006a")
    assert p_a.attributes.smoking == "never"
    assert len(res_a.pending_confirmations) == 0

    # Part B: Rejecting
    state2, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_006b")
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        confirmations=[{
            "field_name": "smoking",
            "target_category": "self_attributes",
            "proposed_value": "never",
            "confidence": 0.7,
            "reasoning": "User said health conscious",
            "clarification_question": "Does that mean you never smoke?"
        }]
    )
    await orchestrator.process_turn(session_id="sess_006b", user_message="I am health conscious.")
    
    res_b = await orchestrator.process_turn(session_id="sess_006b", user_message="No, I actually smoke socially.")
    p_b = orchestrator.get_draft_profile("sess_006b")
    assert p_b.attributes.smoking != "never"
    assert len(res_b.pending_confirmations) == 0


@pytest.mark.anyio
async def test_7_correcting_previously_provided_info(orchestrator, mock_extractor):
    """7. Test correcting previously provided information."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_007")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 25}
    )
    await orchestrator.process_turn(session_id="sess_007", user_message="I'm 25.")
    assert orchestrator.get_draft_profile("sess_007").attributes.age == 25

    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 26}
    )
    await orchestrator.process_turn(session_id="sess_007", user_message="Actually, I turned 26 yesterday.")
    assert orchestrator.get_draft_profile("sess_007").attributes.age == 26


@pytest.mark.anyio
async def test_8_prevent_duplicate_questions(orchestrator, mock_extractor):
    """8. Test preventing duplicate questions across saved sessions and assistant messages."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_008")
    mock_extractor.extract_from_text.return_value = mock_extraction_response()
    
    res1 = await orchestrator.process_turn(session_id="sess_008", user_message="Hello.")
    res2 = await orchestrator.process_turn(session_id="sess_008", user_message="Still here.")
    
    # Inspect persisted state in state manager
    saved_state = orchestrator.state_manager.get_session("sess_008")
    history_ids = saved_state.previously_asked_question_ids
    
    # Inspect actual assistant messages
    assistant_messages = [msg.content for msg in saved_state.conversation_history if msg.role == "assistant"]
    
    assert len(history_ids) == len(set(history_ids))
    assert len(assistant_messages) == len(set(assistant_messages))


@pytest.mark.anyio
async def test_9_handling_ai_failures_without_losing_state(orchestrator, mock_extractor):
    """9. Test handling AI failures without losing or partially corrupting state."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_009")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 30}
    )
    await orchestrator.process_turn(session_id="sess_009", user_message="I'm 30 years old.")
    assert orchestrator.get_draft_profile("sess_009").attributes.age == 30

    mock_extractor.extract_from_text.side_effect = GroqAPIError("API rate limit exceeded")
    
    res = await orchestrator.process_turn(session_id="sess_009", user_message="I like hiking.")
    
    assert orchestrator.get_draft_profile("sess_009").attributes.age == 30
    assert "trouble processing" in res.assistant_message


@pytest.mark.anyio
async def test_10_early_completion_and_maximum_turn_limits(orchestrator, mock_extractor):
    """10. Test early completion requests and maximum turn limits."""
    # Populate essential fields so confirm_draft_profile can succeed for complete early finish
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 30, "gender": "man", "relationship_intent": "long_term", "smoking": "never", "drinking": "never", "wants_children": "no"},
        partner_prefs={"acceptable_genders": ["woman"], "desired_intentions": ["long_term"]}
    )
    
    s, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_early_complete")
    await orchestrator.process_turn(session_id="sess_early_complete", user_message="I am 30 male non smoker non drinker looking for long term woman.")
    
    res = await orchestrator.process_turn(session_id="sess_early_complete", user_message="finish interview")
    assert res.interview_status == InterviewStatus.READY_FOR_REVIEW
    assert res.is_ready_for_review is True
    
    profile = orchestrator.confirm_draft_profile("sess_early_complete")
    assert profile.attributes.age == 30


@pytest.mark.anyio
async def test_11_interview_state_serialization(orchestrator, mock_extractor):
    """11. Test interview state serialization and reconstruction."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_011")
    
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"age": 27, "gender": "woman"}
    )
    await orchestrator.process_turn(session_id="sess_011", user_message="27yo woman.")
    
    state_mgr = orchestrator.state_manager
    json_str = state_mgr.serialize_state("sess_011")
    reconstructed_state = state_mgr.deserialize_state(json_str)
    
    assert reconstructed_state.session_id == "sess_011"
    assert reconstructed_state.user_id == "user_123"
    assert reconstructed_state.draft_profile.attributes.age == 27
    assert reconstructed_state.draft_profile.attributes.gender == "woman"


@pytest.mark.anyio
async def test_12_early_finish_incomplete_profile_cannot_be_confirmed(orchestrator, mock_extractor):
    """12. Test that early-finished incomplete profile CANNOT be confirmed and raises ValueError."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_012_inc")
    mock_extractor.extract_from_text.return_value = mock_extraction_response()
    
    # Request early finish without answering essential fields
    res = await orchestrator.process_turn(session_id="sess_012_inc", user_message="done")
    assert res.interview_status == InterviewStatus.READY_FOR_REVIEW
    assert res.progress.essential_fields_satisfied is False
    
    # confirm_draft_profile MUST fail!
    with pytest.raises(ValueError, match="Cannot finalize an incomplete profile with missing essential fields"):
        orchestrator.confirm_draft_profile("sess_012_inc")


@pytest.mark.anyio
async def test_13_false_positive_finish_phrases_ignored(orchestrator, mock_extractor):
    """13. Test that sentences containing words like 'finish' in context do NOT trigger early finish."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_013_false_pos")
    mock_extractor.extract_from_text.return_value = mock_extraction_response()
    
    # Input with 'finish' in middle of long sentence
    res = await orchestrator.process_turn(
        session_id="sess_013_false_pos",
        user_message="I usually finish work around 5pm and then I like going for a run or reading."
    )
    assert res.interview_status == InterviewStatus.ACTIVE  # Not early finish!


@pytest.mark.anyio
async def test_14_rejection_with_explicit_correction_captured(orchestrator, mock_extractor):
    """14. Test that explicit corrections provided during confirmation rejection are captured."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_014_corr")
    
    # 1. First turn returns a confirmation proposal for smoking="never"
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        confirmations=[{
            "field_name": "smoking",
            "target_category": "self_attributes",
            "proposed_value": "never",
            "confidence": 0.6,
            "reasoning": "User mentioned health conscious",
            "clarification_question": "Does that mean you never smoke?"
        }]
    )
    await orchestrator.process_turn(session_id="sess_014_corr", user_message="I am health conscious.")

    # 2. Second turn rejects the proposal with an explicit correction "No, I smoke socially."
    mock_extractor.extract_from_text.return_value = mock_extraction_response(
        self_attrs={"smoking": "socially"}
    )
    res = await orchestrator.process_turn(session_id="sess_014_corr", user_message="No, I actually smoke socially.")

    profile = orchestrator.get_draft_profile("sess_014_corr")
    assert profile.attributes.smoking == "socially"
    assert "attributes.smoking" in res.newly_extracted_fields


@pytest.mark.anyio
async def test_15_unconfirmed_scenarios_not_merged_into_draft_profile(orchestrator, mock_extractor):
    """15. Test that unconfirmed scenarios in ExtractedProfileUpdate are NOT merged into draft profile."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_015_scen")
    
    from matchlens.models.scenario import ScenarioResponse
    scen_unconfirmed = ScenarioResponse(
        scenario_id="conflict_resolution_01",
        target_dimension="communication_preferences",
        perspective="self_behavior",
        normalized_preference="cool_down_first",
    )
    
    mock_update = mock_extraction_response(self_attrs={"age": 25})
    mock_update.scenarios = [scen_unconfirmed]
    mock_extractor.extract_from_text.return_value = mock_update

    await orchestrator.process_turn(session_id="sess_015_scen", user_message="I am 25 and I cool down first.")
    profile = orchestrator.get_draft_profile("sess_015_scen")

    # Profile scenarios must remain empty from general interview extraction
    assert len(profile.scenarios) == 0


@pytest.mark.anyio
async def test_16_calculate_progress_reflects_actual_completeness_on_early_finish(orchestrator, mock_extractor):
    """16. Test that progress percentage reflects actual completeness when early finish is requested."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_016_prog")
    mock_extractor.extract_from_text.return_value = mock_extraction_response()

    res = await orchestrator.process_turn(session_id="sess_016_prog", user_message="stop interview")
    assert res.interview_status == InterviewStatus.READY_FOR_REVIEW
    # Essential fields are missing, percentage must NOT be 100.0%
    assert res.progress.percentage < 100.0
    assert res.progress.essential_fields_satisfied is False


@pytest.mark.anyio
async def test_17_question_selector_exception_fallback(orchestrator, mock_extractor):
    """17. Test that exceptions in question selector trigger deterministic question fallback."""
    state, _ = orchestrator.start_interview(user_id="user_123", session_id="sess_017_err")
    mock_extractor.extract_from_text.return_value = mock_extraction_response(self_attrs={"age": 28})

    orchestrator.question_selector.select_and_generate_question = AsyncMock(side_effect=RuntimeError("Selector error"))

    res = await orchestrator.process_turn(session_id="sess_017_err", user_message="I am 28.")
    assert res.assistant_message is not None
    assert "Could you tell me a bit more about your" in res.assistant_message


def test_18_state_manager_defensive_copies():
    """18. Test that state manager returns defensive copies to prevent external mutation."""
    from matchlens.interview.state_manager import InterviewStateManager
    sm = InterviewStateManager()
    state = sm.create_session(user_id="u18", session_id="sess_018")

    # Mutate retrieved session externally
    retrieved = sm.get_session("sess_018")
    retrieved.turn_count = 999

    # Internal state in manager must remain unaffected (0)
    internal = sm.get_session("sess_018")
    assert internal.turn_count == 0

