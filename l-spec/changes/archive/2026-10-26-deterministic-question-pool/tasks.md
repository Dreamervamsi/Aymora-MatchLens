## 1. Question Bank & Metadata Schema

- [x] 1.1 Create `QuestionDefinition` dataclass/Pydantic model in `matchlens/interview/question_bank.py` declaring `question_id`, `topic`, `field_key`, `question_text`, `target_category`, `expected_fields`, and `permitted_values`. Verify with unit tests.
- [x] 1.2 Update `QUESTION_BANK` mapping in `question_bank.py` to cover all 6 onboarding categories (`basic_and_intention`, `core_values`, `lifestyle`, `communication`, `partner_expectations`, `dealbreakers`) with declared expected profile fields and permitted canonical values. Verify with unit tests.

## 2. Deterministic Question Selector

- [x] 2.1 Refactor `HybridQuestionSelector` in `matchlens/interview/question_selector.py` to eliminate Groq AI LLM question generation and select questions purely from the deterministic `QUESTION_BANK`.
- [x] 2.2 Implement deterministic fallback, non-repeating question deduplication, and active topic field targeting in `question_selector.py`. Verify `test_interview_orchestration.py` passes without LLM question generation.

## 3. Single-Pass Focused LLM Extraction & Rule Fallbacks

- [x] 3.1 Update `GroqProfileExtractor` in `matchlens/ai/extractor.py` and `RuleProfileExtractor` in `matchlens/interview/rule_extractor.py` to accept expected field targets and permitted value constraints.
- [x] 3.2 Ensure `GroqProfileExtractor` performs at most one focused LLM extraction call per free-text answer and falls back to `RuleProfileExtractor` on timeout, error, or disabled AI extraction.
- [x] 3.3 Ensure simple affirmative/negative confirmation responses and exact scenario choices bypass the LLM entirely and resolve deterministically. Verify with tests in `tests/test_rule_extractor.py` and `tests/test_groq_integration.py`.

## 4. Orchestration & Integration Verification

- [x] 4.1 Update `InterviewOrchestrator` in `matchlens/interview/orchestrator.py` to connect the deterministic question bank and single-pass focused extraction pipeline without altering state machine rules.
- [x] 4.2 Run full test suite (`.venv/bin/pytest`) and verify all tests pass across interview orchestration, rule extraction, state transitions, API endpoints, and matching engine eligibility.
