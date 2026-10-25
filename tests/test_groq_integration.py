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
    GroqMissingKeyError,
    GroqAPIError,
    GroqTimeoutError,
    GroqValidationError,
)


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
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings = GroqSettings(api_key_env_var="GROQ_API_KEY")
    
    with pytest.raises(GroqMissingKeyError):
        GroqClient(settings=settings)


@pytest.mark.anyio
async def test_successful_structured_extraction():
    mock_json = {
        "self_attributes": {
            "age": 28,
            "gender": "man",
            "smoking": "never",
            "interests": ["hiking", "reading"]
        },
        "partner_preferences": {
            "min_age": 24,
            "max_age": 32,
            "acceptable_genders": ["woman"],
            "acceptable_smoking": ["never"]
        },
        "dealbreakers": {
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
    assert result.self_attributes.age == 28
    assert result.self_attributes.gender == "man"
    assert result.self_attributes.smoking == "never"
    assert result.self_attributes.interests == ["hiking", "reading"]
    
    assert result.partner_preferences.min_age == 24
    assert result.partner_preferences.max_age == 32
    assert result.partner_preferences.acceptable_genders == ["woman"]
    
    assert result.dealbreakers.smoking_dealbreaker is True
    assert "drinking" in result.unanswered_fields


@pytest.mark.anyio
async def test_ambiguity_and_confirmation_needed():
    mock_json = {
        "self_attributes": {
            "drinking": "socially"
        },
        "partner_preferences": {},
        "dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": ["User said 'I occasionally party' which might imply drinking or late nights."],
        "confirmations_needed": [
            {
                "field_name": "drinking",
                "inferred_value": "socially",
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
    assert result.confirmations_needed[0].inferred_value == "socially"
    assert len(result.uncertainties) == 1


@pytest.mark.anyio
async def test_timeout_handling():
    mock_async_groq = MagicMock()
    
    async def slow_response(*args, **kwargs):
        await asyncio.sleep(2.0)
        return create_mock_completion_response({})

    mock_async_groq.chat.completions.create = AsyncMock(side_effect=slow_response)

    settings = GroqSettings(timeout_seconds=0.1, max_retries=0)
    client = GroqClient(settings=settings, client=mock_async_groq)

    with pytest.raises(GroqTimeoutError):
        await client.generate_structured(
            prompt="Test prompt",
            system_instruction="Test system",
            response_schema=ExtractedProfileUpdate,
        )


@pytest.mark.anyio
async def test_validation_error_on_invalid_schema():
    mock_invalid_json = {
        "self_attributes": {
            "age": "invalid_not_an_int"
        }
    }

    mock_async_groq = MagicMock()
    mock_async_groq.chat.completions.create = AsyncMock(
        return_value=create_mock_completion_response(mock_invalid_json)
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
async def test_retry_on_transient_failure():
    mock_valid_json = {
        "self_attributes": {"age": 30},
        "partner_preferences": {},
        "dealbreakers": {},
        "scenarios": [],
        "unanswered_fields": [],
        "uncertainties": [],
        "confirmations_needed": []
    }

    mock_async_groq = MagicMock()
    # First call raises an exception, second call succeeds
    mock_async_groq.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("Transient connection reset"),
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

    assert res.self_attributes.age == 30
    assert mock_async_groq.chat.completions.create.call_count == 2
