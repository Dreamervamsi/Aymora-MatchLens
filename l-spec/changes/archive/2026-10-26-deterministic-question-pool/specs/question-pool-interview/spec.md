## Purpose

Provides a zero-AI-question-generation onboarding flow using a deterministic question pool, explicit field targeting, single-pass structured extraction, and AI-free fallbacks.

## ADDED Requirements

### Requirement: Deterministic Question Pool Selection
The system SHALL select all interview questions strictly from a static deterministic question pool covering all 6 interview topics (`basic_and_intention`, `core_values`, `lifestyle`, `communication`, `partner_expectations`, `dealbreakers`). The system SHALL NOT invoke an LLM to generate interview questions.

#### Scenario: Question selection from bank
- **WHEN** the interview orchestrator requests the next question for a given topic and missing field key
- **THEN** the system returns a pre-defined question from the deterministic question pool without making an LLM API call

#### Scenario: No duplicate questions asked
- **WHEN** a question ID or exact question text has already been asked in the active session
- **THEN** the question selector picks an unasked question from the question pool or returns a unique topic-specific fallback

### Requirement: Declared Question Metadata and Expected Schema
Each question in the deterministic question pool SHALL declare its target profile category, target profile field, and expected canonical field values or types.

#### Scenario: Accessing question schema contract
- **WHEN** the profile extractor prepares to process a user's answer to a specific question
- **THEN** it retrieves the expected fields and canonical permitted values declared by that question entry

### Requirement: Single Focused Extraction Call
When extracting structured data from a free-text answer, the system SHALL perform at most one focused LLM extraction call targeting only the fields expected by the active question or topic context. The extracted output MUST be validated against the existing Pydantic models (`ExtractedProfileUpdate`, `UserProfile`).

#### Scenario: Focused LLM extraction
- **WHEN** a free-text user response is received during an interview turn
- **THEN** at most one LLM API call is executed with target field constraints, returning a validated structured JSON profile update

### Requirement: AI-Free Fallbacks for Confirmations, Selections, and Failures
The system SHALL NOT call the LLM for exact selections, simple affirmative/negative confirmations, or scenario options. If an LLM extraction call fails or times out, the system SHALL fallback to deterministic rule-based extraction or explicit-choice prompts without interrupting the session.

#### Scenario: Extraction failure fallback
- **WHEN** an LLM extraction call times out or raises an error
- **THEN** the system executes deterministic rule-based profile extraction, updates state smoothly, and continues onboarding

#### Scenario: Confirmation response without LLM call
- **WHEN** a user responds with "yes" or "no" to a pending confirmation
- **THEN** the system resolves the pending confirmation deterministically without making an LLM call

### Requirement: State Machine and Matching Preservation
The system SHALL preserve all existing interview state transitions, topic progression rules, pending confirmations, draft profile confirmations, and matching engine scoring and eligibility functionality.

#### Scenario: Interview completion and match readiness
- **WHEN** all essential fields across interview topics are satisfied
- **THEN** the interview state transitions to `ready_for_review` and allows draft profile confirmation for matching
