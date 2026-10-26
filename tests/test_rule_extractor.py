import pytest
from matchlens.interview.rule_extractor import RuleProfileExtractor
from matchlens.interview.orchestrator import InterviewOrchestrator
from matchlens.models.profile import UserProfile
from matchlens.ai.models import ExtractedProfileUpdate


@pytest.fixture
def extractor():
    return RuleProfileExtractor()


def test_long_paragraph_multiple_fields(extractor):
    text = (
        "Hello! I am 28 years old, a woman looking for a serious long-term relationship. "
        "I exercise daily, drink socially, and never smoke. "
        "For my partner, I want a man aged between 25 and 35."
    )
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.age == 28
    assert update.confirmed_self_attributes.gender == "woman"
    assert update.confirmed_self_attributes.relationship_intent == "long_term"
    assert update.confirmed_self_attributes.exercise == "daily"
    assert update.confirmed_self_attributes.drinking == "socially"
    assert update.confirmed_self_attributes.smoking == "never"

    assert update.confirmed_partner_preferences.min_age == 25
    assert update.confirmed_partner_preferences.max_age == 35
    assert update.confirmed_partner_preferences.acceptable_genders == ["man"]


def test_age_and_partner_age_and_third_party_distinction(extractor):
    text = "I am 25 years old. My brother is 30. My ideal partner is between 24 and 30."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.age == 25
    assert update.confirmed_partner_preferences.min_age == 24
    assert update.confirmed_partner_preferences.max_age == 30


def test_self_and_partner_preference_distinction(extractor):
    text = "I drink socially, but my partner should not drink."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.drinking == "socially"
    assert update.confirmed_partner_preferences.acceptable_drinking == ["never"]


def test_negated_smoking(extractor):
    text = "I don't smoke and I am a non-smoker."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.smoking == "never"


def test_past_smoking_disregarded(extractor):
    text = "I used to smoke in college, but now I exercise daily."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.smoking is None
    assert update.confirmed_self_attributes.exercise == "daily"


def test_relationship_intent_negation(extractor):
    text = "I am not looking for anything casual, I want a long term relationship."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.relationship_intent == "long_term"


def test_unknown_attributes_remain_null(extractor):
    text = "I like reading books and cooking."
    update = extractor.extract_from_text(text)

    assert update.confirmed_self_attributes.age is None
    assert update.confirmed_self_attributes.smoking is None
    assert update.confirmed_self_attributes.drinking is None
    assert sorted(update.confirmed_self_attributes.interests) == ["cooking", "reading"]


def test_profile_updates_pass_pydantic_validation(extractor):
    text = "I am 30 years old, male, looking for a long term partner. I never drink and never smoke."
    update = extractor.extract_from_text(text)

    assert isinstance(update, ExtractedProfileUpdate)
    assert update.confirmed_self_attributes.age == 30
    assert update.confirmed_self_attributes.gender == "man"


@pytest.mark.anyio
async def test_complete_interview_to_profile_confirmation_flow_without_llm():
    orchestrator = InterviewOrchestrator()
    session, opening_q = orchestrator.start_interview(user_id="test_user_deterministic")

    # Turn 1: Basic info
    res1 = await orchestrator.process_turn(
        session_id=session.session_id,
        user_message="I am 29 years old, female, looking for a long term relationship. I never smoke and never drink and open to kids.",
    )
    assert res1.session_id == session.session_id
    assert "attributes.age" in res1.newly_extracted_fields or "attributes.gender" in res1.newly_extracted_fields

    # Turn 2: Core values
    res2 = await orchestrator.process_turn(
        session_id=session.session_id,
        user_message="My core values are honesty and family.",
    )

    # Turn 3: Partner expectations
    res3 = await orchestrator.process_turn(
        session_id=session.session_id,
        user_message="I am looking for a partner who is a man open to a long term relationship or marriage.",
    )

    state = orchestrator.state_manager.get_session(session.session_id)
    from matchlens.interview.models import InterviewStatus
    state.status = InterviewStatus.READY_FOR_REVIEW
    orchestrator.state_manager.save_session(state)

    confirmed_profile = orchestrator.confirm_draft_profile(session.session_id)
    assert isinstance(confirmed_profile, UserProfile)
    assert confirmed_profile.user_id == "test_user_deterministic"
    assert confirmed_profile.attributes.age == 29
    assert confirmed_profile.attributes.gender == "woman"
    assert confirmed_profile.attributes.smoking == "never"
