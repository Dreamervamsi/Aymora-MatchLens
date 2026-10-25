import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from groq import AuthenticationError, BadRequestError

from matchlens.ai import (
    GroqSettings,
    GroqClient,
    GroqProfileExtractor,
    ExtractedProfileUpdate,
    PartialUserAttributes,
    PartialPartnerPreferences,
    PartialDealbreakers,
    ConfirmationPrompt,
    GroqMissingKeyError,
    GroqAPIError,
    GroqTimeoutError,
    GroqValidationError,
)
from matchlens.models.scenario import ScenarioResponse


def create_mock_completion_response(json_data: dict):
    """Helper to construct a mocked Groq chat completion response."""
    mock_message = MagicMock()
    mock_message.content = json.dumps(json_data)
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.mark.anyio
async def test_missing_api_key_raises_error(monkeypatch):
    """Test 7: Missing API key raises GroqMissingKeyError."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings = GroqSettings(api_key_env_var="GROQ_API_KEY")
    
    with pytest.raises(GroqMissingKeyError):
        GroqClient(settings=settings)


@pytest.mark.anyio
async def test_successful_structured_extraction():
    """Test 8: Successful structured extraction with valid categories."""
    mock_json = {
        "confirmed_self_attributes": {
            "age": 28,
            "gender": "man",
            "smoking": "never",
            "interests": ["hiking", "reading"]
        },
        "confirmed_partner_preferences": {
            "min_age": 24,
            "max_age": 32,
            "acceptable_genders": ["woman"],
            "acceptable_smoking": ["never"]
        },
        "confirmed_dealbreakers": {
            "smoking_dealbreaker": True
        },
        "scenarios": [],
        "unanswered_fields": ["drinking", "wants_children"],
        "uncertainties": [],
        "confirmations_needed": []
    }

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        return_value=create_mock_completion_response(mock_json)
    )

    settings = GroqSettings()
    client = GroqClient(settings=settings, client=mock_async_groq)
    extractor = GroqProfileExtractor(settings=settings, client=client)

    user_text = "I am a 28yo man, non-smoker, into hiking and reading. Looking for a non-smoking woman 24-32. Smoking is a dealbreaker."
    result = await extractor.extract_from_text(user_text)

    assert isinstance(result, ExtractedProfileUpdate)
    assert result.confirmed_self_attributes.age == 28
    assert result.confirmed_self_attributes.gender == "man"
    assert result.confirmed_self_attributes.smoking == "never"
    assert result.confirmed_self_attributes.interests == ["hiking", "reading"]
    
    assert result.confirmed_partner_preferences.min_age == 24
    assert result.confirmed_partner_preferences.max_age == 32
    assert result.confirmed_partner_preferences.acceptable_genders == ["woman"]
    
    assert result.confirmed_dealbreakers.smoking_dealbreaker is True
    assert "drinking" in result.unanswered_fields


@pytest.mark.anyio
async def test_ambiguous_inference_awaiting_confirmation():
    """Test 1: Ambiguous inference placed in confirmations_needed and NOT in confirmed attributes."""
    mock_json = {
        "confirmed_self_attributes": {},
        "confirmed_partner_preferences": {},
        "confirmed_dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": ["User said 'I occasionally party' which might imply social drinking."],
        "confirmations_needed": [
            {
                "field_name": "drinking",
                "target_category": "self_attributes",
                "proposed_value": "socially",
                "confidence": 0.7,
                "reasoning": "User mentioned partying occasionally",
                "clarification_question": "Do you drink socially when partying?"
            }
        ]
    }

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        return_value=create_mock_completion_response(mock_json)
    )

    client = GroqClient(settings=GroqSettings(), client=mock_async_groq)
    extractor = GroqProfileExtractor(client=client)

    result = await extractor.extract_from_text("I occasionally party on weekends.")

    assert len(result.confirmations_needed) == 1
    assert result.confirmations_needed[0].field_name == "drinking"
    assert result.confirmations_needed[0].proposed_value == "socially"
    # Ensure field is NOT set in confirmed_self_attributes
    assert result.confirmed_self_attributes.drinking is None


@pytest.mark.anyio
async def test_invalid_categorical_value_rejection():
    """Test 2: Invalid categorical values fail schema validation."""
    mock_json_invalid_cat = {
        "confirmed_self_attributes": {
            "smoking": "chainsmoker_invalid_category"  # Not in ALLOWED_SMOKING
        },
        "confirmed_partner_preferences": {},
        "confirmed_dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": [],
        "confirmations_needed": []
    }

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        return_value=create_mock_completion_response(mock_json_invalid_cat)
    )

    settings = GroqSettings(max_retries=0)
    client = GroqClient(settings=settings, client=mock_async_groq)

    with pytest.raises(GroqValidationError):
        await client.generate_structured(
            prompt="Test prompt",
            system_instruction="Test system",
            response_schema=ExtractedProfileUpdate,
        )


@pytest.mark.anyio
async def test_unknown_scenario_option_rejection():
    """Test 3: Extracting scenario with unknown scenario option or ID fails validation."""
    mock_async_groq = MagicMock()
    
    # 1. Unknown scenario ID
    client = GroqClient(settings=GroqSettings(), client=mock_async_groq)
    extractor = GroqProfileExtractor(client=client)

    with pytest.raises(ValueError, match="Scenario ID 'unknown_scen_99' is unknown"):
        await extractor.extract_scenario_response(
            scenario_id="unknown_scen_99",
            user_input="I prefer discussing immediately."
        )

    # 2. Unknown option returned by model for valid scenario
    invalid_scenario_response = {
        "scenario_id": "conflict_resolution_01",
        "target_dimension": "communication_preferences",
        "perspective": "self_behavior",
        "normalized_preference": "yell_loudly_unsupported_option" # Not in allowed options
    }
    mock_async_groq.chat.completions.create = AsyncMock(
        return_value=create_mock_completion_response(invalid_scenario_response)
    )

    with pytest.raises(GroqValidationError):
        await extractor.extract_scenario_response(
            scenario_id="conflict_resolution_01",
            user_input="I yell loudly."
        )


@pytest.mark.anyio
async def test_transient_provider_failure_and_retry():
    """Test 4: Transient failure retries and succeeds."""
    mock_valid_json = {
        "confirmed_self_attributes": {"age": 30},
        "confirmed_partner_preferences": {},
        "confirmed_dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": [],
        "confirmations_needed": []
    }

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("Transient connection reset 503"),
            create_mock_completion_response(mock_valid_json)
        ]
    )

    settings = GroqSettings(max_retries=2)
    client = GroqClient(settings=settings, client=mock_async_groq)

    res = await client.generate_structured(
        prompt="Test prompt",
        system_instruction="Test system",
        response_schema=ExtractedProfileUpdate,
    )

    assert res.confirmed_self_attributes.age == 30
    assert mock_async_groq.chat.completions.create.call_count == 2


@pytest.mark.anyio
async def test_permanent_provider_failure_without_retry():
    """Test 5: Permanent failure (e.g. 401 AuthenticationError) fails immediately without retry."""
    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        side_effect=AuthenticationError(
            message="Invalid Groq API key",
            response=MagicMock(status_code=401),
            body={}
        )
    )

    settings = GroqSettings(max_retries=3)
    client = GroqClient(settings=settings, client=mock_async_groq)

    with pytest.raises(GroqAPIError, match="Permanent Groq API error"):
        await client.generate_structured(
            prompt="Test prompt",
            system_instruction="Test system",
            response_schema=ExtractedProfileUpdate,
        )

    # Must fail on call 1 without attempting retries!
    assert mock_async_groq.chat.completions.create.call_count == 1


@pytest.mark.anyio
async def test_invalid_json_and_schema_validation():
    """Test 6: Malformed JSON output triggers GroqValidationError."""
    mock_message = MagicMock()
    mock_message.content = "NOT_A_JSON_STRING {{ bad_format"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(return_value=mock_response)

    settings = GroqSettings(max_retries=0)
    client = GroqClient(settings=settings, client=mock_async_groq)

    with pytest.raises(GroqValidationError):
        await client.generate_structured(
            prompt="Test prompt",
            system_instruction="Test system",
            response_schema=ExtractedProfileUpdate,
        )


@pytest.mark.anyio
async def test_timeout_handling():
    """Test GroqTimeoutError when call exceeds timeout_seconds."""
    mock_async_groq = MagicMock()
    
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(2.0)
        return create_mock_completion_response({})

    mock_async_groq.chat.completions.create = AsyncMock(side_effect=slow_response)

    settings = GroqSettings(timeout_seconds=0.05, max_retries=0)
    client = GroqClient(settings=settings, client=mock_async_groq)

    with pytest.raises(GroqTimeoutError):
        await client.generate_structured(
            prompt="Test prompt",
            system_instruction="Test system",
            response_schema=ExtractedProfileUpdate,
        )


@pytest.mark.anyio
async def test_unconfirmed_inference_in_confirmed_fields_contract_rejection():
    """Test contract validator: placing a field in confirmed attributes while also requiring confirmation fails validation."""
    invalid_payload = {
        "confirmed_self_attributes": {
            "drinking": "socially"  # Placed in confirmed_self_attributes!
        },
        "confirmed_partner_preferences": {},
        "confirmed_dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": [],
        "confirmations_needed": [
            {
                "field_name": "drinking",
                "target_category": "self_attributes",
                "proposed_value": "socially",
                "confidence": 0.6,
                "reasoning": "Inferred from party mention",
                "clarification_question": "Do you drink socially?"
            }
        ]
    }

    with pytest.raises(ValueError, match="marked as requiring confirmation"):
        ExtractedProfileUpdate.model_validate(invalid_payload)
