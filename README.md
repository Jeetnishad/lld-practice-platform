# LLD Practice Platform

A focused, rubric-based Low-Level Design practice application that helps engineering candidates design, submit, and receive explainable feedback on LLD interview problems.

---

## Problem

Engineers preparing for system design interviews struggle to practice LLD because:
- No structured platform gives **explainable, rubric-based feedback**
- Most resources only show reference solutions — no feedback on *why* a design is good or bad
- Practice is unstructured: whiteboard sessions or reading, with no iteration loop

## Solution

LLD Practice Platform provides:

- **5 realistic interview-grade LLD problems** (Parking Lot, Elevator, Vending Machine, Movie Booking, Splitwise)
- **Structured submission workspace** (classes, responsibilities, interfaces, relationships, explanation, edge cases)
- **8-criterion rubric evaluation** with evidence, concern, suggestion, and confidence per criterion
- **AI evaluation** via OpenAI (with graceful rule-based fallback)
- **Attempt history** with improvement tracking across attempts

---

## Features

| Feature | Description |
|---------|-------------|
| Problem library | 5 LLD problems with full requirements and assumptions |
| Practice workspace | Structured class/interface/relationship editor |
| Evaluation | Rule-based + AI evaluation via 8-criterion rubric |
| Explainable feedback | Evidence from submission, concern, suggestion, confidence |
| Fallback mode | Works without AI API key (rule-based evaluator) |
| Attempt history | Track all attempts, scores, and improvements |
| Try again | Retry any problem; see score improvement |
| Retry evaluation | Re-evaluate failed evaluations |
| Zero authentication | Demo mode — start practising immediately |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, Vite, TypeScript, Tailwind CSS v4, React Router |
| Backend | Python 3.10+, Flask 3.0, SQLAlchemy 2.0 |
| Validation | Pydantic v2 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | OpenAI GPT-4o via abstraction layer |
| Testing | pytest, pytest-flask |

---

## Architecture

```
React Frontend (Vite)
       ↓
REST API (Flask Blueprints)
       ↓
Application Service Layer (PracticeService)
       ↓  ↓
Domain Layer    Evaluator Abstraction
       ↓            ├── AIEvaluator          (production)
Repository Layer    ├── RuleBasedEvaluator   (fallback / offline)
       ↓            └── MockEvaluator        (testing only)
SQLite / PostgreSQL
```

---

## Project Structure

```
project/
├── frontend/               # React + Vite frontend
│   └── src/
│       ├── pages/          # Dashboard, Problems, Workspace, Feedback, History
│       ├── components/     # Navbar, Badge, Button, Card, UI
│       ├── services/       # API service layer
│       └── types/          # TypeScript domain types
├── backend/
│   ├── app/
│   │   ├── domain/         # Pure domain entities (no DB dependency)
│   │   ├── evaluators/     # BaseEvaluator, Mock, RuleBased, AI, Factory
│   │   ├── api/            # Flask routes
│   │   ├── repositories.py # DB access layer
│   │   ├── services.py     # Application service
│   │   ├── models.py       # SQLAlchemy ORM models
│   │   └── schemas.py      # Pydantic validation + serializers
│   ├── tests/              # pytest test suite (52 tests)
│   ├── seed.py             # Database seed script
│   └── run.py              # Entry point
├── README.md
├── DESIGN.md
├── RESEARCH.md
├── AI_USAGE.md
└── .env.example
```

---

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+

### 1. Clone the repository

```bash
git clone <repository-url>
cd project
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment variables

```bash
# Copy the example
cp ../.env.example .env

# Edit .env — set your OpenAI key if you want AI evaluation
# Leave EVALUATOR_TYPE=rule_based for fallback mode
```

### 4. Initialize and seed database

```bash
python seed.py
```

### 5. Start backend

```bash
python run.py
# Runs at http://localhost:5000
```

### 6. Frontend setup

```bash
cd ../frontend
npm install
npm run dev
# Runs at http://localhost:5173
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `development` | App environment |
| `SECRET_KEY` | `dev-secret-key-...` | Flask secret key |
| `DATABASE_URL` | `sqlite:///lld_platform.db` | Database URI |
| `EVALUATOR_TYPE` | `rule_based` | `ai`, `rule_based`, or `mock` |
| `OPENAI_API_KEY` | _(empty)_ | OpenAI key for AI evaluation |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model to use |
| `AI_TIMEOUT` | `30` | API timeout in seconds |
| `FRONTEND_URL` | `http://localhost:5173` | CORS origin |

---

## Running Tests

```bash
cd backend
venv\Scripts\activate   # or source venv/bin/activate
python -m pytest tests/ -v
```

**52 tests** covering:
- Problem retrieval (6 tests)
- Attempt creation and history (8 tests)
- Submission (7 tests)
- Evaluation and retry (7 tests)
- Evaluator abstraction (5 tests)
- MockEvaluator (5 tests)
- RuleBasedEvaluator (8 tests)
- AI output validation (5 tests — no API key needed)

---

## AI Configuration

**With AI (recommended for best experience):**

```env
EVALUATOR_TYPE=ai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
```

**Without AI (fallback — works out of the box):**

```env
EVALUATOR_TYPE=rule_based
```

The UI clearly indicates which evaluator produced the feedback.

---

## Fallback Evaluator

**Startup-level fallback**: When `EVALUATOR_TYPE=ai` is configured but `OPENAI_API_KEY` is missing
or the `AIEvaluator` cannot be initialised, the factory automatically substitutes
`RuleBasedEvaluator`. No change to application code is needed.

**Runtime fallback**: If `AIEvaluator` is active but fails during a specific evaluation
(timeout, API error, rate limit, malformed JSON response, or Pydantic validation failure),
`AIEvaluator` automatically delegates to `RuleBasedEvaluator` and returns a completed
evaluation with `is_fallback=True`. The learner receives scores and feedback without
any retry required.

If `RuleBasedEvaluator` itself also fails (rare), the evaluation is marked `failed`,
the attempt is marked `failed`, and the learner can retry via
`POST /api/attempts/:id/evaluation/retry`.

**Rule-based evaluation properties**:
- Scores are based on submission structure, keyword analysis, class count, etc.
- All 8 rubric criteria are still populated with evidence, concerns, suggestions
- The UI shows **"Fallback Evaluation"** badge — never presents fallback feedback as AI

> **Note**: `MockEvaluator` is used exclusively in the test suite and is never active
> in development or production environments.


---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/problems` | List all problems |
| GET | `/api/problems/:id` | Problem detail (by ID or slug) |
| POST | `/api/attempts` | Start new attempt |
| GET | `/api/attempts` | List attempts (by learner_id) |
| GET | `/api/attempts/:id` | Get attempt detail |
| POST | `/api/attempts/:id/submissions` | Submit solution |
| GET | `/api/attempts/:id/evaluation` | Get evaluation |
| POST | `/api/attempts/:id/evaluation/retry` | Retry failed evaluation |

---

## Production Build

```bash
cd frontend
npm run build
# Output in frontend/dist/
```

---

## Deployment

**Backend (Render/Railway):**
1. Set environment variables (see above)
2. Use `DATABASE_URL=postgresql://...` for production
3. Start command: `gunicorn run:app`

**Frontend (Vercel):**
1. Build command: `npm run build`
2. Output dir: `dist`
3. Set `VITE_API_URL` to your backend URL

---

## Limitations

- No authentication — single shared demo learner (`demo-learner`)
- Background evaluation runs in a thread (not a job queue — see DESIGN.md)
- Rule-based evaluator uses heuristics, not semantic understanding
- AI evaluation quality depends on GPT-4o output (validated with Pydantic)

## Future Improvements

- User authentication (JWT or OAuth)
- Code submission format (actual OOP class definitions)
- Human evaluator workflow
- Celery/Redis for background job queue at scale
- Diagram submission (Mermaid/PlantUML)
- Problem difficulty progression tracking
- PostgreSQL full-text search for feedback history
