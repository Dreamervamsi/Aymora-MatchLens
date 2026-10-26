# batch-profile-extraction Specification

## Purpose
Defines single-batch AI profile extraction occurring strictly after completing conversational question-pool interview turns.

## Requirements

### Requirement: Zero AI Invocations During Interview Turns
The system SHALL collect all user interview responses chronologically through the deterministic question bank without invoking Groq API calls on individual turns.

#### Scenario: Turn-by-turn answer submission
- **WHEN** a user submits an answer to an interview question
- **THEN** the system stores the question-answer pair in the session state without executing any AI extraction call

### Requirement: Single Batch AI Extraction Execution
When all required interview questions are answered, the system SHALL transition into a `processing_extraction` status and send all chronological question-answer pairs to Groq in exactly one structured extraction request.

#### Scenario: Batch extraction trigger
- **WHEN** the final interview question is answered
- **THEN** the interview status transitions to `processing_extraction` and a single Groq extraction call is initiated

### Requirement: Strict Pydantic Schema Validation & Normalization
The system SHALL validate Groq's extracted JSON response against the existing backend Pydantic models (`UserAttributes`, `PartnerPreferences`, `Dealbreakers`). The system MUST NOT auto-assign unstated defaults like `min_age = 18` or `max_age = 120` or force default boolean dealbreaker constraints.

#### Scenario: Valid response extraction
- **WHEN** Groq returns structured JSON matching `attributes`, `expectations`, and `dealbreakers`
- **THEN** the values are parsed into `UserProfile` and the session status transitions to `ready_for_review`

#### Scenario: Extraction failure or timeout
- **WHEN** Groq returns invalid JSON or times out
- **THEN** the system preserves all collected QA history, stays in an editable/retryable state, and allows user-triggered retries without re-asking questions

### Requirement: Explicit Profile Review Confirmation
The system SHALL display the extracted draft profile on the Profile Review page and require explicit user confirmation before marking the interview state as `completed` or persisting to matchmaking storage.

#### Scenario: Profile review confirmation
- **WHEN** the user reviews and explicitly confirms their draft profile
- **THEN** the interview status becomes `completed` and the profile is saved for matching
