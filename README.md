# MatchLens — AI-Assisted Reciprocal Matchmaking MVP

MatchLens is a scenario-aware, reciprocal compatibility web application and engine.

Unlike traditional one-directional recommendation algorithms, MatchLens evaluates relationship compatibility bidirectionally:
1. **User A $\rightarrow$ Candidate B**: How well Candidate B satisfies User A's preferences and scenario expectations.
2. **Candidate B $\rightarrow$ User A**: How well User A satisfies Candidate B's preferences and scenario expectations.
3. **Reciprocal Compatibility Score**: Geometric mean combining both directional scores:
   $$S_{\text{mutual}}(A,B) = \sqrt{S(A \rightarrow B) \times S(B \rightarrow A)}$$

---

## Complete User Journey

The MatchLens MVP guides users through a 4-step onboarding-to-matching workflow:

1. **Step 1 — Welcome & Session Setup (`/`)**:
   - Initializes user session identity (`userId`).
   - Introduces the platform vision and reciprocal matchmaking architecture.
2. **Step 2 — Conversational Interview Onboarding (`/interview`)**:
   - Adaptive AI conversational onboarding powered by Groq LLM (`openai/gpt-oss-120b`).
   - Collects personal attributes, lifestyle habits, partner preferences, and mandatory dealbreakers.
   - Highlights extracted traits and handles confirmation prompts in natural dialogue.
3. **Step 3 — Profile Review & Explicit Confirmation (`/profile/review`)**:
   - Displays structured extracted traits, partner expectations, and dealbreakers.
   - Explicit confirmation saves the verified profile to the backend repository (`POST /api/v1/interview/{session_id}/confirm`).
4. **Step 4 — Scenario-Based Relationship Assessment (`/assessment`)**:
   - Presents 3 real-world decision scenarios:
     - `conflict_resolution_01`: Handling disagreement after a stressful day.
     - `social_energy_01`: Weekend downtime preferences.
     - `financial_planning_01`: Approach to joint budgeting and major expenses.
   - Captures independent responses for **BOTH** self-behavior and partner-expectation per scenario.
   - Reviews and confirms responses before attaching them to the user profile (`POST /api/v1/assessment/{assessment_id}/confirm`).
5. **Step 5 — Reciprocal Match Discovery (`/matches`)**:
   - Strictly verifies completed profile and scenario assessment prerequisites.
   - Calls `GET /api/v1/matches/{user_id}?top_k=3`.
   - Filters candidate pool against mandatory dealbreakers (age, gender, relationship intent, smoking, children, blocklist).
   - Renders top eligible candidates with bidirectional scores, evidence coverage, and detailed compatibility breakdowns.

---

## Technology Stack

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: Tailwind CSS v4 + Lucide React Icons
- **Routing**: React Router v7 (`BrowserRouter`)
- **HTTP Client**: Native `fetch` API abstraction (`apiClient.js`)
- **State & Persistence**: `WorkflowContext` + browser `sessionStorage` (resilient to page refreshes)
- **Testing**: Vitest + React Testing Library + `@testing-library/jest-dom`

### Backend
- **Framework**: Python 3.11+ + FastAPI
- **Validation**: Pydantic v2 schemas
- **AI Integration**: Groq API client wrapper (`openai/gpt-oss-120b`)
- **Data Persistence**: In-memory thread-safe repositories (`ProfileRepository`, `AssessmentStateManager`, `InterviewStateManager`)
- **Matching Engine**: Deterministic reciprocal compatibility ranker with geometric mean scoring and mutual dealbreaker eligibility filtering

---

## Environment Variables & Configuration

Create a `.env` file in the project root or frontend/backend directories based on `.env.example`:

### Server-Side (Backend) Environment Variables
```env
# Required for Groq AI Profile Extraction & Conversational Interview
GROQ_API_KEY="gsk_your_groq_api_key_here"

# Optional Groq Settings
GROQ_MODEL_NAME="openai/gpt-oss-120b"
GROQ_TEMPERATURE="0.2"

# API & CORS Settings
CORS_ORIGINS='["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]'
```

### Client-Side (Frontend) Environment Variables
`frontend/.env.example`:
```env
# API Base URL (defaults to http://localhost:8000 if omitted)
VITE_API_BASE_URL="http://localhost:8000"
```

> **Security Note**: The `GROQ_API_KEY` is strictly server-side and is **never** exposed in frontend code or Vite client bundles.

---

## Local Development & Startup Instructions

### 1. Clone & Setup Backend
```bash
# Navigate to repository root
cd /path/to/Aymora-MatchLens

# Create virtual environment and activate
python -m venv .venv
source .venv/bin/activate

# Install package in editable mode with dependencies
pip install -e .

# Set Groq API Key
export GROQ_API_KEY="your_groq_api_key"

# Run FastAPI Server (Single Worker required for in-memory repositories)
uvicorn matchlens.api.app:app --reload --port 8000
```
- Backend API will be available at: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`

### 2. Setup & Start Frontend
```bash
# Navigate to frontend directory
cd /path/to/Aymora-MatchLens/frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```
- Frontend application will be available at: `http://localhost:5173`

---

## Automated Testing Commands

### Backend Pytest Suite
```bash
# Run all backend unit & integration tests from repository root
pytest
```

### Frontend Vitest Suite & Linting
```bash
cd frontend

# Run frontend unit & component integration tests
npm run test

# Run ESLint check
npm run lint

# Verify production Vite build
npm run build
```

---

## In-Memory Repository Assumptions & Demo Data

- **Single-Worker Requirement**: The MVP backend uses thread-safe in-memory session repositories (`ProfileRepository`, `AssessmentStateManager`, `InterviewStateManager`). When running the API server, execute Uvicorn with a **single worker process** (`--workers 1` or default `uvicorn`) so all endpoints access the same repository instance.
- **Backend Restarts**: Restarting the FastAPI backend process clears in-memory state. Users can re-run the interview/assessment onboarding flow in under 2 minutes.
- **Demonstration Seed Candidates**: The reciprocal matching engine automatically loads a set of pre-configured synthetic candidate profiles (`matchlens/synthetic/profiles.py`) alongside any confirmed profiles in the repository, ensuring realistic reciprocal matching demonstrations out-of-the-box.
- **No Fabricated Data**: The frontend renders only actual backend recommendations and eligible profiles without inventing fake profile photos, bios, or swipe metrics.

---

## Deployment Considerations

- **Single Process Hosting**: Deploy backend as a single container or server instance (e.g. Render, Railway, AWS ECS) using a single Uvicorn worker process.
- **SPA Routing Fallback**: Configure web host (e.g. Vercel, Netlify, Nginx) to redirect all non-file route requests to `/index.html` for client-side React Router navigation.
- **Production API Base URL**: Set `VITE_API_BASE_URL` in frontend build environment to point to the deployed FastAPI backend HTTPS domain.

---

## Known MVP Limitations

- **In-Memory Storage**: Data persistence resets upon server restart (by design for this challenge MVP; no SQL/Redis databases required).
- **Fixed Scenario Catalog**: The current assessment uses 3 core canonical relationship scenarios (`conflict_resolution_01`, `social_energy_01`, `financial_planning_01`).
- **No Authentication**: User sessions are identified via lightweight `userId` tokens stored in `sessionStorage` rather than full OAuth/JWT user authentication.
