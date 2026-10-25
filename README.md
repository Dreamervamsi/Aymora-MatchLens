# MatchLens — Core Reciprocal Compatibility Engine

MatchLens is a scenario-aware, reciprocal compatibility engine built as a proposed enhancement for Aymora's matchmaking platform.

Unlike traditional one-directional recommendation algorithms, MatchLens evaluates compatibility bidirectionally:
1. How well **Candidate B** satisfies **User A's** preferences $S(A \rightarrow B)$.
2. How well **User A** satisfies **Candidate B's** preferences $S(B \rightarrow A)$.
3. A final reciprocal compatibility score combining both directional scores using a **geometric mean** $S_{\text{mutual}}(A,B) = \sqrt{S(A \rightarrow B) \times S(B \rightarrow A)}$.

---

## Architecture Overview

MatchLens is engineered using Python 3.11+, Pydantic v2, and pure deterministic comparison functions. It includes a Groq AI integration layer (`openai/gpt-oss-120b`) for structured natural language profile extraction and stateful interview orchestration.

```
matchlens/
├── config.py                 # System defaults, dimensions, and coverage thresholds
├── models/
│   ├── profile.py            # User profile schema (Attributes, Expectations, Dealbreakers, Weights)
│   ├── scenario.py           # Scenario definitions, responses, and centralized ScenarioCatalog
│   └── scoring.py            # Score contract models (MatchResult, DirectionalScore, EvidenceRecord)
├── engine/
│   ├── eligibility.py        # Three-state mutual mandatory filtering ('eligible', 'ineligible', 'pending_information')
│   ├── dimension_scorers.py  # Pure deterministic dimension comparison functions & scenario blending
│   ├── directional.py        # Directional weighted compatibility calculation & single-pass execution
│   ├── reciprocal.py         # Geometric mean score aggregation & evidence summary synthesis
│   └── ranker.py             # Candidate profile ranking with deterministic tie-breaking & deduplication
├── ai/
│   ├── client.py             # AsyncGroq API client wrapper with JSON schema enforcement & retry backoff
│   ├── config.py             # GroqSettings (GROQ_API_KEY, model_name='openai/gpt-oss-120b')
│   ├── extractor.py          # GroqProfileExtractor (Structured update extraction & scenario response evaluation)
│   ├── models.py             # Extraction contracts (ExtractedProfileUpdate, ConfirmationPrompt)
│   └── interview/            # Phase 5.2 Stateful Conversational Onboarding Package
│       ├── config.py         # InterviewSettings (turn limits, topic turn caps, essential fields)
│       ├── models.py         # InterviewState, InterviewStatus, ChatMessage, PendingConfirmation, InterviewTurnResult
│       ├── orchestrator.py   # InterviewOrchestrator pipeline & process_turn atomic execution
│       ├── question_bank.py  # Deterministic question bank per topic & missing field key
│       ├── question_selector.py # Hybrid Question Selector (Groq AI dynamic wording + bank fallback)
│       └── state_manager.py  # In-memory session registry & Pydantic JSON serialization
└── synthetic/
    └── profiles.py           # Realistic synthetic adult profiles for testing and demonstration
```

---

## Phase 5.2 — AI Conversational Onboarding Interview Architecture

MatchLens Phase 5.2 introduces a stateful, adaptive conversational onboarding interview that collects meaningful relationship information through natural dialogue:

### 1. Interview Topics Progression
The interview covers topics progressively across turns:
- `BASIC_AND_INTENTION`: Age, gender, relationship intention.
- `CORE_VALUES`: Core values, religion/beliefs, relationship priorities.
- `LIFESTYLE`: Habits (smoking, drinking, exercise, children).
- `COMMUNICATION`: Communication style, conflict resolution, contact frequency.
- `PARTNER_EXPECTATIONS`: Expectations regarding partner age, habits, communication.
- `DEALBREAKERS`: Explicit mandatory non-negotiables.

### 2. Confirmation Contract & Ambiguity Handling
- **Explicit vs. Inferred**: Unambiguous statements directly update confirmed profile fields (`confirmed_self_attributes`, `confirmed_partner_preferences`).
- **Unconfirmed Proposals**: Inferred or ambiguous traits are placed in `confirmations_needed` and held in `pending_confirmations`. They are **NEVER** placed into confirmed profile attributes until the user confirms them.
- **Explicit Yes/No & Ambiguity Resolution**: Affirmative/negative responses are parsed with regex word boundaries. Ambiguous, qualified, or contradictory answers (*"maybe"*, *"yes and no"*) remain pending and re-ask the clarification question.

### 3. Interview Lifecycle States (`InterviewStatus`)
- **`ACTIVE`**: Ongoing conversation moving through topics.
- **`AWAITING_CONFIRMATION`**: Paused to clarify an ambiguous inference with the user.
- **`READY_FOR_REVIEW`**: Triggered when essential fields are satisfied, topic turn limit reached, or user requests early finish (*"/finish"*, *"done"*).
- **`COMPLETED`**: Reserved for when the user explicitly reviews and confirms their draft profile (`confirm_draft_profile()`). Incomplete early-finished profiles cannot be finalized until essential fields are satisfied.

---

## Groq Setup & Configuration

Configure the Groq API key in your environment variable:

```bash
export GROQ_API_KEY="your-groq-api-key-here"
```

The system defaults to `openai/gpt-oss-120b` via Groq's high-speed inference engine with JSON schema enforcement, automatic retry backoff, and local Pydantic validation.

---

## Quickstart & Demonstration

### 1. Install Dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Run Automated Test Suite
```bash
pytest
```

### 3. Run Matching Engine Demonstration
```bash
python examples/demo.py
```

### 4. Run AI Conversational Interview Interactive CLI Demo
```bash
python examples/interview_demo.py
```

---

## Core Scoring Formulas & Rules

### 1. Directional Weighted Compatibility
$$S(A \rightarrow B) = \frac{\sum_{i \in \text{active}} w_{A,i} \cdot s_i(A,B)}{\sum_{i \in \text{active}} w_{A,i}}$$

### 2. Reciprocal Geometric Mean Compatibility
$$S_{\text{mutual}}(A,B) = \sqrt{S(A \rightarrow B) \times S(B \rightarrow A)}$$

### 3. Evidence Coverage Score
$$\text{evidence\_coverage} = \left(\frac{W_{\text{active}}}{W_{\text{total}}}\right) \times 100\%$$
