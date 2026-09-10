# AI/LLM Usage Transparency

This document explains how AI tools were used in this project, in compliance with the assignment's transparency requirements.

---

## LLM Usage in the Product

### AIEvaluator (`backend/app/evaluators/ai_evaluator.py`)

The AI Evaluator sends a structured prompt to OpenAI's GPT-4o model to generate
rubric-based feedback on a candidate's LLD submission.

**Prompt Design:**
- System prompt defines the 8-criterion rubric and scoring guidelines
- User message includes: problem description, assumptions, all class definitions,
  interfaces, relationships, design explanation, and edge cases
- Response format is specified as JSON matching `AIEvaluationResponse` schema
- Temperature is 0.2 to reduce hallucinations while allowing nuanced feedback

**Validation:**
- All AI output is validated through Pydantic (`AIEvaluationResponse`)
- Score bounds (0–10 per criterion, 0–100 overall) are enforced via `Field(ge=0, le=10)`
- Any AI failure (timeout, API error, rate limit, malformed JSON, or Pydantic validation
  failure) causes `AIEvaluator` to delegate to `RuleBasedEvaluator`, returning a
  completed evaluation with `is_fallback=True`
- Only if `RuleBasedEvaluator` also fails does the evaluation become `failed`,
  which the learner can retry

**Transparency in UI:**
- Feedback cards display the evaluator source
- AI evaluations show "AI Evaluation" badge (cyan)
- Fallback evaluations show "Fallback Evaluation" badge (violet)
- `is_fallback` field is exposed in the API response

---

## Development Assistance

This project was developed with AI coding assistance (Google Gemini).
The following areas involved AI-assisted development:

| Area | AI Involvement |
|------|---------------|
| Project scaffolding | Vite + Flask setup commands and configuration |
| Domain entity design | Dataclass definitions for Problem, Attempt, Submission, Evaluation |
| SQLAlchemy model definitions | ORM model structure and relationships |
| Repository pattern | CRUD implementations and domain mapping |
| Evaluator implementations | MockEvaluator, RuleBasedEvaluator, AIEvaluator logic |
| Pydantic schemas | Request/response validation models |
| Flask routes | API endpoint handlers |
| React components | UI component implementations |
| Test cases | pytest test design and implementation |
| Documentation | README.md, DESIGN.md structure |

All generated code was reviewed, understood, debugged (e.g., threading app context fix,
duplicate submission 409 routing fix), and verified through automated tests and manual E2E testing.

---

## Developer Judgement and Final Decisions

AI coding assistance was used throughout development — for scaffolding, implementation,
testing, and documentation. AI was not used as a passive tool; suggestions were actively
evaluated, modified, or rejected based on the project's design goals.

Final architecture and engineering decisions were reviewed and selected by the developer.
The final project was manually reviewed and tested end-to-end before submission.

Specific decisions made by the developer:

1. **Architecture choice**: Modular monolith over microservices for this scope
2. **Strategy pattern for evaluators**: BaseEvaluator interface design
3. **Repository pattern boundaries**: What goes in service vs. repository vs. domain
4. **Threading fix**: Capturing `flask_app._get_current_object()` before thread start
5. **Duplicate submission error design**: `DuplicateSubmissionError` as distinct exception type
6. **Rubric design**: 8 criteria mapping, scoring weights, confidence levels
7. **Fallback chain**: AI → RuleBased (at startup if API key missing; at runtime if AI call fails), with `is_fallback` transparency in the UI

---

## AI Suggestions and Final Engineering Decisions

The following examples illustrate where AI suggestions were reviewed and a conscious
engineering decision was made.

---

**1. Evaluator Abstraction**

**Problem:** How to support multiple evaluation strategies (AI, rule-based, testing) without coupling service logic to any specific evaluator.

**AI Suggestion:** Add an `if/elif` block in the service layer to select evaluation logic based on a config flag.

**Final Decision:** Define a `BaseEvaluator` abstract class with a concrete `evaluate()` method, and inject the selected evaluator into the service at startup via a factory.

**Why:** The Strategy pattern keeps the service layer unaware of which evaluator is active, making it trivially swappable and independently testable.

**Trade-off:** More files and indirection upfront, but evaluation strategy can be changed at startup without modifying service code.

---

**2. Background Evaluation**

**Problem:** Evaluation via OpenAI can take several seconds. The HTTP response must not block on it.

**AI Suggestion:** Use `asyncio` or a task queue (Celery + Redis) to offload evaluation.

**Final Decision:** Use `threading.Thread` with the Flask `app` instance captured before the thread starts (`current_app._get_current_object()`), and persist the submission before the thread begins.

**Why:** For a 2-day MVP, threading is sufficient and requires zero additional infrastructure. Celery/Redis would add real operational complexity with no user-visible benefit at this scale.

**Trade-off:** No retry-on-crash guarantee across process restarts. Mitigated by exposing `POST /evaluation/retry` and persisting submissions before evaluation begins.

---

**3. Structured Text Submission**

**Problem:** What format should learners use to submit their LLD design?

**AI Suggestion:** Accept free-form text or a code file upload.

**Final Decision:** Accept a structured JSON payload with named fields: `assumptions`, `classes` (with name, responsibility, methods, notes), `interfaces`, `relationships`, `design_explanation`, and `edge_cases`.

**Why:** Structured input makes evaluation more consistent. Both the AI evaluator and the rule-based evaluator can operate against the same representation, and the `to_text_summary()` method serialises it cleanly for the prompt.

**Trade-off:** Less expressive than a diagram or real code, but significantly simpler and more reliable for the MVP timeframe.

---

**4. Rule-Based Fallback**

**Problem:** What happens when the AI evaluator is unavailable (missing API key at startup, or service deployed without OpenAI credentials)?

**AI Suggestion:** Return an error to the learner if AI is unavailable.

**Final Decision:** The factory (`evaluator_factory.py`) detects a missing API key at startup and transparently substitutes `RuleBasedEvaluator`. At runtime, if `AIEvaluator` fails (timeout, API error, malformed response, or Pydantic validation failure), it delegates to `RuleBasedEvaluator` and returns a completed evaluation with `is_fallback=True` — the learner receives feedback without needing to retry. The UI shows a "Fallback Evaluation" badge so the learner always knows the source.

**Why:** The platform should be usable offline and during API outages. A deterministic fallback is always better than a complete failure for learning workflows.

**Trade-off:** Rule-based scores are heuristic, not semantic. This is clearly disclosed in the UI via the `is_fallback` flag.

---

**5. Repository Abstraction**

**Problem:** How to prevent SQLAlchemy ORM models from leaking into service and evaluator code.

**AI Suggestion:** Pass SQLAlchemy model objects directly to the service layer.

**Final Decision:** Introduce repository classes (`ProblemRepository`, `AttemptRepository`, etc.) with a private `_map_*(model)` function that converts each ORM model to a pure domain dataclass before returning it. The service layer never imports SQLAlchemy.

**Why:** Domain entities are pure Python dataclasses that can be instantiated and tested without a database session. Evaluators receive domain objects, keeping them free of infrastructure concerns.

**Trade-off:** Requires maintaining a mapping layer between ORM models and domain entities, but this is a single, narrow translation point per repository.
