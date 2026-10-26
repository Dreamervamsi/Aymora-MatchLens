# MatchLens Groq AI Integration Documentation

## Overview
The `matchlens.ai` package provides a structured, asynchronous natural-language extraction pipeline using Groq (`openai/gpt-oss-20b`). It translates unstructured conversational onboarding input into validated MatchLens Pydantic models while respecting missing data (`None`) and flagging ambiguous statements for confirmation.

---

## Key Modules & Classes

- `GroqSettings`: Configures environment variable (`GROQ_API_KEY`), model (`openai/gpt-oss-20b`), timeout (`timeout_seconds`), retries (`max_retries`), temperature (`temperature`), and reasoning effort (`reasoning_effort`).
- `GroqClient`: Async Groq SDK wrapper supporting provider-side `json_schema` response format (with automatic fallback to `json_object`), fast failure on permanent 4xx errors, transient backoff retries, and strict local Pydantic validation.
- `GroqProfileExtractor`: Core extraction service that turns natural language into `ExtractedProfileUpdate` objects or scenario-bound `ScenarioResponse` objects.
- `ExtractedProfileUpdate`: Structured contract explicitly separating confirmed facts from proposed inferences:
  - `confirmed_self_attributes`: `PartialUserAttributes` (only explicitly stated, unambiguous facts)
  - `confirmed_partner_preferences`: `PartialPartnerPreferences` (only explicitly stated, unambiguous partner preferences)
  - `confirmed_dealbreakers`: `PartialDealbreakers` (explicitly stated hard dealbreakers)
  - `scenarios`: `List[ScenarioResponse]` (validated scenario assessments)
  - `unanswered_fields`: `List[str]` (relevant fields left unstated)
  - `uncertainties`: `List[str]` (vague/ambiguous statements)
  - `confirmations_needed`: `List[ConfirmationPrompt]` (unconfirmed inferences requiring user verification)

---

## Contract Safety Guarantee
`ExtractedProfileUpdate` enforces a Pydantic model validator that forbids placing any field listed in `confirmations_needed` into `confirmed_self_attributes`, `confirmed_partner_preferences`, or `confirmed_dealbreakers`. Unconfirmed inferences MUST be approved by the user before being merged into their profile.

---

## Categorical Normalization
All categorical fields are validated against standard MatchLens allowed value sets:
- `smoking`: `never`, `socially`, `regularly`
- `drinking`: `never`, `socially`, `regularly`
- `exercise`: `daily`, `weekly`, `rarely`, `never`
- `wants_children`: `yes`, `no`, `open`, `maybe`
- `relationship_intent`: `long_term`, `marriage`, `casual`, `friendship`
- `communication_style`: `direct`, `gentle`, `expressive`, `analytical`
- `conflict_resolution`: `discuss_immediately`, `cool_down_first`, `written_first`
- `contact_frequency`: `frequent`, `daily_check_in`, `as_needed`

---

## Usage Example for Onboarding Flow Orchestration (Phase 5.2)

```python
import asyncio
from matchlens.ai import GroqProfileExtractor, GroqSettings
from matchlens.models import UserProfile

async def process_user_onboarding_turn():
    settings = GroqSettings(model_name="openai/gpt-oss-20b")
    extractor = GroqProfileExtractor(settings=settings)

    user_answer = (
        "I'm 29, never smoke, and like hiking. "
        "Looking for someone 25-33 who wants a long-term relationship. "
        "Smoking is a dealbreaker. I occasionally drink socially."
    )
    context_question = "Tell us about yourself and what you're looking for."

    extracted_update = await extractor.extract_from_text(
        user_input=user_answer,
        context_prompt=context_question,
    )

    # 1. Apply confirmed facts to profile
    existing_profile = UserProfile(user_id="user_123")
    
    if extracted_update.confirmed_self_attributes.age is not None:
        existing_profile.attributes.age = extracted_update.confirmed_self_attributes.age
    if extracted_update.confirmed_self_attributes.smoking is not None:
        existing_profile.attributes.smoking = extracted_update.confirmed_self_attributes.smoking

    if extracted_update.confirmed_partner_preferences.min_age is not None:
        existing_profile.expectations.min_age = extracted_update.confirmed_partner_preferences.min_age

    if extracted_update.confirmed_dealbreakers.smoking_dealbreaker is not None:
        existing_profile.dealbreakers.smoking_dealbreaker = extracted_update.confirmed_dealbreakers.smoking_dealbreaker

    # 2. Present unconfirmed inferences to the user for clarification
    for prompt in extracted_update.confirmations_needed:
        print(f"Clarification Question for field '{prompt.field_name}': {prompt.clarification_question}")

if __name__ == "__main__":
    asyncio.run(process_user_onboarding_turn())
```

---

## Scenario Catalog Extraction Example

```python
scenario_response = await extractor.extract_scenario_response(
    scenario_id="conflict_resolution_01",
    user_input="I always prefer to take an hour to cool down before discussing disagreements."
)
# Returns ScenarioResponse validated against ScenarioCatalog
```

---

## Error Handling

All exceptions derive from `GroqError`:
- `GroqMissingKeyError`: Raised if `GROQ_API_KEY` is missing.
- `GroqTimeoutError`: Raised if request exceeds timeout limit.
- `GroqPermanentAPIError`: Raised immediately on 4xx client errors (401, 400, 403, 404) without retrying.
- `GroqAPIError`: Raised on transient network/provider errors after max retries are exhausted.
- `GroqValidationError`: Raised if response fails JSON decoding, category validation, or Pydantic contract checks.
