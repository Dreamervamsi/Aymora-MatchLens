## Why

To minimize Groq API costs, latency, and turn-by-turn processing failures during matchmaking onboarding, MatchLens is shifting from turn-by-turn LLM extraction to a single structured batch extraction executed after all interview questions are collected via the deterministic question pool.

## What Changes

- **Zero LLM Extraction During Interview Turns**: Eliminate all Groq API calls during individual question-and-answer turns. Answers are collected chronologically in the session state.
- **Single Batch Extraction Execution**: Once all interview questions across required topics are answered, transition the session into an extraction processing state (`PROCESSING_EXTRACTION`). Send all collected question-answer pairs in a single structured JSON extraction request to Groq.
- **Exact Pydantic Schema Validation**: Validate and normalize Groq's response directly into existing `UserAttributes`, `PartnerPreferences`, and `Dealbreakers` models without guessing or auto-assigning default restrictions.
- **Idempotent State Transition & Recovery**: Ensure extraction is idempotent. If extraction fails, preserve all session history and present a dedicated retry option. Upon success, transition state to `READY_FOR_REVIEW` for explicit user confirmation.

## Capabilities

### New Capabilities
- `batch-profile-extraction`: Single batch AI extraction workflow executing after complete question pool interview completion.

### Modified Capabilities
<!-- None -->

## Impact

- `matchlens/ai/extractor.py`: Add batch extraction method `extract_full_profile_batch` implementing required system prompt, rules, and single Groq structured output call.
- `matchlens/interview/orchestrator.py`: Remove turn-by-turn extraction calls in `process_turn`; trigger batch extraction upon interview completion; manage `PROCESSING_EXTRACTION` status.
- `matchlens/interview/models.py` & `schemas.py`: Ensure `PROCESSING_EXTRACTION` status is supported where applicable.
- `matchlens/api/routers/interview.py`: Support batch extraction trigger and idempotent session recovery.
