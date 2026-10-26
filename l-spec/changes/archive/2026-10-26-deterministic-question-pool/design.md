## Context

Currently, `HybridQuestionSelector` attempts to generate dynamic interview questions using Groq AI before falling back to `QUESTION_BANK`. Additionally, `GroqProfileExtractor` invokes Groq LLM calls on every interview turn even when the input is standard or when rule extraction suffices. To optimize cost, throughput, and reliability, MatchLens is moving to a 100% deterministic question bank for interview question selection and single-pass focused LLM extraction with deterministic rule fallbacks.

## Goals / Non-Goals

**Goals:**
- Zero LLM calls for question generation. Serve all interview questions directly from an enhanced `QUESTION_BANK`.
- Define a structured question model in `QUESTION_BANK` mapping each question to its expected profile fields (`target_category`, `target_field`, `expected_fields`) and permitted canonical values (e.g., `ALLOWED_SMOKING`, `ALLOWED_DRINKING`, `ALLOWED_RELATIONSHIP_INTENT`).
- Execute at most one focused LLM extraction call per free-text answer, constrained to the target question's declared fields and validated against existing Pydantic models.
- Avoid AI entirely for exact selections, simple affirmative/negative confirmations, and scenario options.
- Ensure extraction failure or timeout gracefully falls back to `RuleProfileExtractor` and explicit-choice prompts without throwing exceptions or corrupting interview state.
- Preserve all existing interview state management (`InterviewState`, `InterviewStateManager`, `InterviewStatus`), pending confirmation workflows, and matching engine APIs.

**Non-Goals:**
- Modifying the Phase 5 scenario assessment extractor (`GroqScenarioExtractor`) or matching engine scoring algorithms.
- Changing Pydantic schema structures for `UserProfile`, `UserAttributes`, `PartnerPreferences`, or `Dealbreakers`.

## Decisions

### 1. Structure Question Bank Definitions
Represent entries in `QUESTION_BANK` as structured objects (`QuestionDefinition`) containing:
- `question_id`: Unique identifier (e.g., `basic_and_intention.age`).
- `topic`: `InterviewTopic`.
- `field_key`: Associated field (e.g., `age`, `smoking`, `acceptable_genders`).
- `question_text`: Friendly phrasing.
- `target_category`: `"self_attributes"`, `"partner_preferences"`, or `"dealbreakers"`.
- `expected_fields`: List of profile field names expected from answers to this question.
- `permitted_values`: Allowed canonical value strings or enum values.

### 2. Refactor `HybridQuestionSelector`
- Convert `HybridQuestionSelector` into a lightweight, fully deterministic component.
- Remove Groq client dependencies and LLM calls from `select_and_generate_question`.
- Look up question definitions strictly from `QUESTION_BANK` by `(target_topic, missing_field_key)`.
- Enforce non-repeating question history filtering deterministically using `state.previously_asked_question_ids` and conversation history.

### 3. Focused Single-Pass Extraction & Rule Fallback
- `GroqProfileExtractor.extract_from_text` will accept target field constraints derived from the active question's `expected_fields` and `permitted_values`.
- Prioritize deterministic pre-checks: simple affirmative/negative responses to confirmations bypass the LLM entirely and use rule processing.
- If `GroqProfileExtractor` is invoked, execute at most 1 focused LLM extraction. If the LLM call times out, fails, or is disabled, immediately fall back to `RuleProfileExtractor.extract_from_text`.

### 4. Wire Deterministic Pipeline into `InterviewOrchestrator`
- `process_turn`: Bypasses AI question generation completely.
- When `use_ai_extraction=False` or when extraction fails, state transitions seamlessly.
- State preservation: `working_state` deep copy rollback on unexpected errors remains active.

## Risks / Trade-offs

- [Risk] Fixed questions may feel slightly less conversational than dynamically phrased AI questions.
  → Mitigation: Design warm, natural, polished question phrasing in `QUESTION_BANK`.
- [Risk] Rule extractor might miss nuanced free-text phrasing.
  → Mitigation: LLM extraction remains the primary single-pass call when AI extraction is enabled, with `RuleProfileExtractor` acting as the robust zero-latency fallback.
