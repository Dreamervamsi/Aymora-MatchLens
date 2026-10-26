## Why

To significantly reduce LLM call frequency, latency, and operational cost during user onboarding interviews, MatchLens needs to replace dynamic AI question generation with a deterministic question bank. Each interview question must be pre-selected from a static question pool, explicitly declaring its target profile fields, expected fields, and allowed canonical values.

## What Changes

- **Deterministic Question Selection**: Never call the LLM to generate the next interview question. Select all interview questions strictly from the question pool across all 6 onboarding categories (`basic_and_intention`, `core_values`, `lifestyle`, `communication`, `partner_expectations`, and `dealbreakers`).
- **Structured Field Contract & Single Focused LLM Extraction**: Questions declare expected profile fields and allowed categorical value enums. Free-text user answers invoke at most one focused LLM extraction call returning only those target fields in structured JSON, validated with existing Pydantic models (`ExtractedProfileUpdate`, `UserProfile`).
- **Deterministic AI-Free Fallbacks**: Avoid AI entirely for exact selections, confirmations, and scenario options. If LLM extraction fails or times out, immediately fallback to deterministic rule-based extraction / explicit-choice fallbacks so onboarding remains fully functional without throwing errors.
- **State & Matching Preservation**: Preserve all existing interview state transitions, pending confirmations, topic progression, and matching/eligibility engine compatibility.

## Capabilities

### New Capabilities
- `question-pool-interview`: Deterministic question selection and structured single-pass extraction pipeline for onboarding interviews.

### Modified Capabilities
<!-- None -->

## Impact

- `matchlens/interview/question_bank.py`: Extended with structured question definitions declaring expected profile fields, allowed canonical values, and category mappings.
- `matchlens/interview/question_selector.py`: Refactored to completely eliminate LLM calls during question generation and serve deterministic question selection.
- `matchlens/ai/extractor.py` & `matchlens/interview/rule_extractor.py`: Updated to enforce focused extraction contracts, field targeting, and deterministic fallbacks on failure/timeout.
- `matchlens/interview/orchestrator.py`: Updated to wire deterministic selection, focused extraction, and explicit fallbacks without modifying state machine rules or matching capabilities.
