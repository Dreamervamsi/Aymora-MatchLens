# MatchLens — Scenario-Based Assessment Lifecycle (Phase 5.3)

## Overview

Phase 5.3 introduces a structured, stateful assessment module (`matchlens/assessment/`) for evaluating reciprocal compatibility using hypothetical relationship scenarios.

For each selected scenario in `ScenarioCatalog`, the system separately collects:
1. **Self Behavior**: What the user would most likely do in the situation.
2. **Partner Expectation**: What the user prefers or is comfortable with their partner doing in the same situation.

---

## Assessment State Machine

An assessment session progresses through clear state and stage transitions:

```
                          ┌───────────────────────────┐
                          │    start_assessment()     │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   Stage: SELF_BEHAVIOR    │
                          └─────────────┬─────────────┘
                                        │ submit_response()
                                        ▼
                          ┌───────────────────────────┐
                          │ Stage: PARTNER_EXPECTATION│
                          └─────────────┬─────────────┘
                                        │ (repeat for all scenarios)
                                        ▼
                          ┌───────────────────────────┐
                          │  Status: READY_FOR_REVIEW │
                          │       Stage: REVIEW       │
                          └─────────────┬─────────────┘
                                        │ confirm_assessment()
                                        ▼
                          ┌───────────────────────────┐
                          │     Status: COMPLETED     │
                          │      Stage: COMPLETED     │
                          └───────────────────────────┘
```

---

## Key Components

### 1. `ScenarioCatalog`
Centralized metadata definitions containing scenario IDs, target dimensions, allowed option keys, and user-facing prompts.

MVP Scenarios:
- `conflict_resolution_01` (target dimension: `communication_preferences`)
- `social_energy_01` (target dimension: `lifestyle_compatibility`)
- `financial_planning_01` (target dimension: `core_values`)

### 2. `ScenarioAssessmentOrchestrator`
Main orchestration API for conducting scenario assessments:

- `start_assessment(user_id, selected_scenario_ids=None) -> AssessmentTurnResult`
- `submit_response(assessment_id, user_response) -> AssessmentTurnResult`
- `correct_response(assessment_id, scenario_id, target, new_value) -> AssessmentTurnResult`
- `get_assessment_state(assessment_id) -> AssessmentState`
- `get_completed_responses(assessment_id) -> List[ScenarioResponse]`
- `confirm_assessment(assessment_id) -> AssessmentTurnResult`

### 3. AI Normalization & Clarification
`GroqScenarioExtractor` attempts exact option matching first. For natural language answers, it uses Groq structured extraction to map user input to `ScenarioCatalog.allowed_options`.
- If interpretation is ambiguous or confidence < 0.7, a `ClarificationRequest` is attached to state, prompting the user to clarify before advancing.
- If AI is unavailable or fails, the orchestrator falls back to presenting standard options directly.

### 4. Canonical `ScenarioResponse`
When confirmed, scenario answers are converted into canonical `ScenarioResponse` objects:
- `perspective`: `"self_behavior"`
- `normalized_preference`: User's validated self choice.
- `expected_partner_preference`: User's validated partner expectation choice.
- `target_dimension`: Catalog dimension.
- `importance`: Weighting factor (default: 1.0).

### 5. Profile Integration
`attach_scenario_responses(profile, responses, replace_existing=False) -> UserProfile` attaches confirmed responses to an existing `UserProfile` without mutating the original profile.

---

## Usage Example

```python
from matchlens.assessment import ScenarioAssessmentOrchestrator, attach_scenario_responses
from matchlens.models.profile import UserProfile

# 1. Initialize orchestrator and session
orchestrator = ScenarioAssessmentOrchestrator()
turn = orchestrator.start_assessment(user_id="user_123")
aid = turn.assessment_id

# 2. Submit responses for self and partner
await orchestrator.submit_response(aid, "cool_down_first")        # Self
await orchestrator.submit_response(aid, "discuss_immediately")   # Partner
# ... (repeat for remaining scenarios)

# 3. Confirm assessment
orchestrator.confirm_assessment(aid)
responses = orchestrator.get_completed_responses(aid)

# 4. Attach to user profile
user_profile = UserProfile(user_id="user_123")
updated_profile = attach_scenario_responses(user_profile, responses)
```
