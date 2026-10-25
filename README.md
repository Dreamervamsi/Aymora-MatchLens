# MatchLens — Core Reciprocal Compatibility Engine

MatchLens is a scenario-aware, reciprocal compatibility engine built as a proposed enhancement for Aymora's matchmaking platform.

Unlike traditional one-directional recommendation algorithms, MatchLens evaluates compatibility bidirectionally:
1. How well **Candidate B** satisfies **User A's** preferences $S(A \rightarrow B)$.
2. How well **User A** satisfies **Candidate B's** preferences $S(B \rightarrow A)$.
3. A final reciprocal compatibility score combining both directional scores using a **geometric mean** $S_{\text{mutual}}(A,B) = \sqrt{S(A \rightarrow B) \times S(B \rightarrow A)}$.

---

## Architecture Overview

MatchLens is engineered using Python 3.11+, Pydantic v2, and pure deterministic comparison functions. It requires no external AI API calls or database infrastructure, making it lightweight and easily importable into a FastAPI backend.

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
└── synthetic/
    └── profiles.py           # Realistic synthetic adult profiles for testing and demonstration
```

---

## Core Scoring Formulas & Rules

### 1. Directional Weighted Compatibility
$$S(A \rightarrow B) = \frac{\sum_{i \in \text{active}} w_{A,i} \cdot s_i(A,B)}{\sum_{i \in \text{active}} w_{A,i}}$$

Where:
- $w_{A,i}$ is User A's importance weight for dimension $i$.
- $s_i(A,B)$ is the normalized score [0 - 100] measuring how well Candidate B satisfies User A's expectations in dimension $i$.
- Dimensions missing sufficient data are excluded from active weights, preventing missing answers from acting as negative signals.

### 2. Reciprocal Geometric Mean Compatibility
$$S_{\text{mutual}}(A,B) = \sqrt{S(A \rightarrow B) \times S(B \rightarrow A)}$$

The geometric mean penalizes asymmetric matches where compatibility is one-sided (e.g., $96$ and $30$ yields $\approx 53.67$ rather than an arithmetic mean of $63.0$).

### 3. Evidence Coverage Score
$$\text{evidence\_coverage} = \left(\frac{W_{\text{active}}}{W_{\text{total}}}\right) \times 100\%$$

Pairs where either direction falls below `min_evidence_coverage` (default 60%) are flagged with `is_low_coverage = True` and excluded from confident Top-K candidate recommendations.

---

## Dimension Weights & Default Ratios

| Dimension | Default Weight |
|---|---:|
| Core Values | 35% |
| Relationship Intentions | 25% |
| Lifestyle Compatibility | 15% |
| Communication Preferences | 15% |
| Shared Interests | 10% |

---

## Scenario-Based Compatibility Heuristic

MatchLens integrates scenario assessments generated during AI onboarding interviews:
- Scenario responses compare Evaluator's explicit partner expectations (`expected_partner_preference` or `perspective == "partner_expectation"`) against Candidate's self-reported behavior (`perspective == "self_behavior"`).
- Scenario alignment is evaluated deterministically using scenario importance weights without double-counting.
- **Notice**: Scenario matching is a rule-based categorical similarity heuristic designed for traceable evidence generation, and is NOT a psychological diagnosis or behavioral model.

---

## Quickstart & Execution

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

### 3. Run Interactive Demonstration
```bash
python examples/demo.py
```

---

## FastAPI Backend Integration Plan

To integrate MatchLens into a FastAPI backend:
1. **Endpoint**: `POST /api/v1/matches/rank`
2. **Request Body**: `{"requesting_user": UserProfile, "candidates": List[UserProfile], "top_k": 3}`
3. **Response**: Return serialized `MatchResult` objects along with structured `EvidenceRecord` items. Downstream Gemini LLM services can directly consume `EvidenceRecord` list to generate personalized explanation text.
