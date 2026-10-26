## 1. Interview Models & Status Updates

- [x] 1.1 Add `PROCESSING_EXTRACTION = "processing_extraction"` to `InterviewStatus` enum in `matchlens/interview/models.py` and update `matchlens/api/schemas.py`. Verify with tests.

## 2. Groq Batch Extractor Implementation

- [x] 2.1 Implement `SYSTEM_BATCH_EXTRACTION_PROMPT` containing rules 1–22 in `matchlens/ai/extractor.py`. Verify prompt structure against requirements.
- [x] 2.2 Implement `extract_full_profile_batch(conversation_history)` in `GroqProfileExtractor` in `matchlens/ai/extractor.py`, returning structured JSON validated into `ExtractedProfileUpdate`. Fallback to `RuleProfileExtractor` or raise structured exception on failure. Verify with unit tests in `tests/test_groq_integration.py`.

## 3. Interview Orchestrator & State Machine Updates

- [x] 3.1 Update `InterviewOrchestrator.process_turn` in `matchlens/interview/orchestrator.py` to remove turn-by-turn AI extraction calls, ensuring zero LLM API calls during standard question-answer turns.
- [x] 3.2 Update `InterviewOrchestrator` to execute batch profile extraction once the final question is answered or when early finish is requested, transitioning through `PROCESSING_EXTRACTION` to `READY_FOR_REVIEW`.
- [x] 3.3 Add `execute_batch_extraction(session_id)` method to `InterviewOrchestrator` supporting idempotent batch extraction execution and retries. Verify with tests in `tests/test_interview_orchestration.py`.

## 4. API Endpoints & Verification

- [x] 4.1 Expose `POST /api/interview/{session_id}/extract_batch` endpoint in `matchlens/api/routers/interview.py` for idempotent batch extraction and retries.
- [x] 4.2 Run full pytest suite (`.venv/bin/pytest`) and verify all 100+ tests pass across API, orchestration, rule extraction, and matching engine eligibility.
