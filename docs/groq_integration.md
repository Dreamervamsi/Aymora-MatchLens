# MatchLens Groq AI Integration Documentation

## Overview
The `matchlens.ai` package provides a structured, asynchronous natural-language extraction pipeline using Groq (`openai/gpt-oss-120b`). It translates unstructured conversational onboarding input into validated MatchLens Pydantic models while respecting missing data (`None`) and flagging ambiguous statements for confirmation.

---

## Key Modules & Classes

- `GroqSettings`: Configures environment variable (`GROQ_API_KEY`), model (`openai/gpt-oss-120b`), timeout (`timeout_seconds`), retries (`max_retries`), and temperature (`temperature`).
- `GroqClient`: Async Groq SDK wrapper that enforces JSON schema formatting, handles retries with backoff, and validates response schema.
- `GroqProfileExtractor`: Core extraction service that turns natural language into `ExtractedProfileUpdate` objects.
- `ExtractedProfileUpdate`: Structured output contract separating:
  - `self_attributes`: `PartialUserAttributes`
  - `partner_preferences`: `PartialPartnerPreferences`
  - `dealbreakers`: `PartialDealbreakers`
  - `scenarios`: `List[ScenarioResponse]`
  - `unanswered_fields`: `List[str]`
  - `uncertainties`: `List[str]`
  - `confirmations_needed`: `List[ConfirmationPrompt]`

---

## Usage Example for Onboarding Flow Orchestration (Phase 5.2)

```python
import asyncio
from matchlens.ai import GroqProfileExtractor, GroqSettings
from matchlens.models import UserProfile, UserAttributes, PartnerPreferences, Dealbreakers

async def process_user_onboarding_turn():
    # 1. Initialize extraction service (reads GROQ_API_KEY from environment)
    settings = GroqSettings(model_name="openai/gpt-oss-120b")
    extractor = GroqProfileExtractor(settings=settings)

    # 2. Receive user answer in natural language
    user_answer = (
        "I'm a 29 year old non-smoker who loves cooking and running. "
        "I am looking for someone between 25 and 33 who wants a long term relationship. "
        "Smoking is definitely a dealbreaker for me."
    )
    context_question = "Tell us about yourself and what you're looking for in a partner."

    # 3. Extract structured profile update
    extracted_update = await extractor.extract_from_text(
        user_input=user_answer,
        context_prompt=context_question,
    )

    # 4. Check for ambiguous statements needing user confirmation
    if extracted_update.confirmations_needed:
        for prompt in extracted_update.confirmations_needed:
            print(f"Clarification needed on {prompt.field_name}: {prompt.clarification_question}")

    # 5. Apply extracted updates to an existing or new UserProfile
    existing_profile = UserProfile(user_id="user_123")
    
    # Merge self attributes
    if extracted_update.self_attributes.age is not None:
        existing_profile.attributes.age = extracted_update.self_attributes.age
    if extracted_update.self_attributes.smoking is not None:
        existing_profile.attributes.smoking = extracted_update.self_attributes.smoking

    # Merge partner expectations
    if extracted_update.partner_preferences.min_age is not None:
        existing_profile.expectations.min_age = extracted_update.partner_preferences.min_age
    if extracted_update.partner_preferences.max_age is not None:
        existing_profile.expectations.max_age = extracted_update.partner_preferences.max_age

    # Merge dealbreakers
    if extracted_update.dealbreakers.smoking_dealbreaker is not None:
        existing_profile.dealbreakers.smoking_dealbreaker = extracted_update.dealbreakers.smoking_dealbreaker

    print("Updated Profile:", existing_profile)

if __name__ == "__main__":
    asyncio.run(process_user_onboarding_turn())
```

---

## Error Handling

All exceptions derive from `GroqError`:
- `GroqMissingKeyError`: Raised if `GROQ_API_KEY` is missing.
- `GroqTimeoutError`: Raised if request exceeds timeout limit.
- `GroqAPIError`: Raised on provider API/network errors.
- `GroqValidationError`: Raised if response fails JSON decoding or Pydantic validation.
