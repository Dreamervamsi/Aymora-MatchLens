## Context

Currently, `InterviewOrchestrator` invokes `GroqProfileExtractor.extract_from_text` during every interview turn. To transition to a single batch extraction workflow, turn-by-turn AI extraction will be completely removed. The system will collect all question-answer turns in `InterviewState.conversation_history`. Once all topics/questions are answered or max turns reached, `InterviewOrchestrator` triggers a single batch extraction call using the exact system prompt rules requested.

## Goals / Non-Goals

**Goals:**
- Eliminate turn-by-turn LLM calls. Turn processing will be zero-latency local state recording.
- Implement `extract_full_profile_batch(conversation_history: List[ChatMessage]) -> ExtractedProfileUpdate` in `GroqProfileExtractor`.
- Add exact system prompt rules specified in the prompt contract (rules 1–22, 3 top-level objects: `attributes`, `expectations`, `dealbreakers`).
- Add/support `PROCESSING_EXTRACTION` status in `InterviewStatus` enum and API schemas.
- Trigger single batch extraction at the end of the interview. If extraction succeeds, transition state to `READY_FOR_REVIEW`.
- If extraction fails/times out, maintain session history and support idempotent retry endpoint (`POST /api/interview/{session_id}/extract_batch`).
- Preserve existing Pydantic validation on `UserProfile`, `UserAttributes`, `PartnerPreferences`, and `Dealbreakers`.
- Preserve existing profile review and confirmation APIs (`POST /api/interview/{session_id}/confirm`).

**Non-Goals:**
- Modifying scenario assessment logic or reciprocal matching scoring algorithms.
- Modifying frontend UI templates (backend API contract remains fully backward-compatible).

## Decisions

### 1. New Batch Extraction System Prompt
`SYSTEM_BATCH_EXTRACTION_PROMPT` in `matchlens/ai/extractor.py` will encapsulate all 22 rules:
- Strict output JSON contract with top-level `attributes`, `expectations`, and `dealbreakers`.
- Direct mapping into Pydantic models.
- Rules prohibiting guessing default values like `min_age=18` or forcing boolean dealbreakers.

### 2. State Machine Transitions
1. `ACTIVE`: Collecting Q&A turns deterministically.
2. `PROCESSING_EXTRACTION`: Final question answered or interview finished early. Batch extraction initiated.
3. `READY_FOR_REVIEW`: Batch extraction succeeded, draft profile populated.
4. `COMPLETED`: User explicitly confirms profile.

### 3. API Router Endpoints
- `POST /api/interview/{session_id}/turn`: Submits user response, returns next deterministic question. When interview completes, triggers batch extraction and returns `status="processing_extraction"` or `status="ready_for_review"`.
- `POST /api/interview/{session_id}/extract_batch`: Idempotent batch extraction trigger/retry endpoint.

## Risks / Trade-offs

- [Risk] Groq API may time out or return malformed JSON for long conversation histories.
  → Mitigation: Bounded timeout, single structured call, and explicit retry endpoint without repeating Q&A turns.
