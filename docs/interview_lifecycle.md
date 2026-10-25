# MatchLens Phase 5.2 — AI Conversational Interview Lifecycle

## Overview

Phase 5.2 introduces a stateful, adaptive conversational onboarding interview engine for MatchLens. The orchestrator engages users in natural dialogue, extracts structured compatibility attributes via Groq AI (`openai/gpt-oss-120b`), isolates unconfirmed inferences, and generates a review-ready `UserProfile`.

---

## Architecture Components

1. **`InterviewState` (`matchlens.interview.models`)**:
   Pydantic model encapsulating `session_id`, `user_id`, `status`, `current_topic`, `conversation_history`, `draft_profile`, `pending_confirmations`, `previously_asked_question_ids`, `turn_count`, and `progress`. Fully JSON-serializable and reconstructable.

2. **`InterviewOrchestrator` (`matchlens.interview.orchestrator`)**:
   Core pipeline executing `start_interview` and `process_turn`. Manages atomic state progression, explicit confirmation parsing, profile updates validation, and hybrid question selection.

3. **`HybridQuestionSelector` (`matchlens.interview.question_selector`)**:
   Generates context-aware follow-up questions using Groq API with fallback to deterministic `question_bank.py` on API errors or timeouts.

4. **`InterviewStateManager` (`matchlens.interview.state_manager`)**:
   In-memory state management and JSON serialization registry.

---

## Interview Lifecycle States (`InterviewStatus`)

```
                  ┌──────────────────────┐
                  │        ACTIVE        │
                  └──────────┬───────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
┌──────────────────────┐          ┌──────────────────────┐
│AWAITING_CONFIRMATION │          │   READY_FOR_REVIEW   │
└──────────┬───────────┘          └──────────┬───────────┘
           │                                 │
           └────────────────►────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │      COMPLETED       │
                  └──────────────────────┘
```

1. **`ACTIVE`**: Conversation is actively progressing through interview topics (`BASIC_AND_INTENTION` -> `CORE_VALUES` -> `LIFESTYLE` -> `COMMUNICATION` -> `PARTNER_EXPECTATIONS` -> `DEALBREAKERS`).
2. **`AWAITING_CONFIRMATION`**: Placed on hold when an ambiguous or low-confidence inference is proposed. The user must confirm or reject the proposed value before it enters the confirmed profile.
3. **`READY_FOR_REVIEW`**: Essential fields have been collected, topic turn limit reached, or the user requested an early finish ("done", "finish").
4. **`COMPLETED`**: Reserved for when the user explicitly reviews and confirms their draft profile (`confirm_draft_profile`).

---

## Turn Pipeline (`process_turn`)

```
User Message
    │
    ▼
[Atomic State Copy] ──► Early Finish Check ("done", "finish")
    │
    ├─► [Active Confirmation?] ─┬─► Explicit Yes ─► Validate & Apply
    │                           ├─► Explicit No  ─► Reject & Clear
    │                           └─► Ambiguous   ─► Re-ask & Halt
    │
    ├─► [General Groq Extractor] ──► Pydantic Model Validation ──► Merge Confirmed Data
    │
    ├─► [Topic Turn Check] ──► Advance Topic if Complete
    │
    └─► [Question Selection] ──► Topic-Scoped Missing Field ──► Non-repeating Question
```

---

## Example Usage

```python
from matchlens.interview import InterviewOrchestrator, InterviewStatus

orchestrator = InterviewOrchestrator()

# 1. Start session
state, opening_msg = orchestrator.start_interview(user_id="user_123")
print("Assistant:", opening_msg)

# 2. Process turn
turn_result = await orchestrator.process_turn(
    session_id=state.session_id,
    user_message="I'm a 28 year old man looking for a long term relationship."
)

print("Status:", turn_result.interview_status)
print("Assistant:", turn_result.assistant_message)

# 3. Complete and finalize when ready
if turn_result.is_ready_for_review:
    final_profile = orchestrator.confirm_draft_profile(state.session_id)
    print("Final Profile User ID:", final_profile.user_id)
```
