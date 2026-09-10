"""
MockEvaluator — returns deterministic, realistic-looking feedback instantly.

Used for:
  - Unit tests (fast, no DB, no AI)
  - CI/CD pipeline
  - Demo mode when neither AI nor rule-based is needed
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.domain.entities import Evaluation, Problem, RubricCriterion, Submission
from app.evaluators.base import BaseEvaluator, RUBRIC_CRITERIA


_MOCK_CRITERIA = [
    RubricCriterion(
        name="Requirement Understanding",
        score=7.0,
        evidence="The submission addresses core functional requirements including the main entities and their interactions.",
        concern="Some edge requirements such as concurrent access or error states may not be fully addressed.",
        suggestion="Re-read the requirements and ensure every bullet point is reflected in at least one class or interface.",
        confidence="high",
        display_order=0,
    ),
    RubricCriterion(
        name="Class Responsibilities",
        score=6.5,
        evidence="Primary entities are identified and given distinct responsibilities.",
        concern="Some classes may be taking on multiple responsibilities (SRP violation risk).",
        suggestion="Review each class and ask: 'Does this class have exactly one reason to change?' Split where needed.",
        confidence="medium",
        display_order=1,
    ),
    RubricCriterion(
        name="Encapsulation & Interfaces",
        score=6.0,
        evidence="Public/private distinction is implied in method descriptions.",
        concern="No explicit interfaces or abstract classes are described, which limits substitutability.",
        suggestion="Define at least one interface for a key abstraction point (e.g., PaymentProcessor, NotificationService).",
        confidence="medium",
        display_order=2,
    ),
    RubricCriterion(
        name="Coupling & Cohesion",
        score=6.5,
        evidence="Classes reference each other through composition rather than global state.",
        concern="High coupling may exist between the main controller class and domain objects.",
        suggestion="Use dependency injection to decouple components and improve testability.",
        confidence="medium",
        display_order=3,
    ),
    RubricCriterion(
        name="Abstraction / Design Patterns",
        score=5.5,
        evidence="Basic OOP patterns are used. Factory or Strategy patterns may be implicit.",
        concern="No explicit design patterns are named or justified.",
        suggestion="Identify 1–2 design patterns applicable to this problem and explain why you chose them.",
        confidence="low",
        display_order=4,
    ),
    RubricCriterion(
        name="Extensibility",
        score=6.0,
        evidence="Core entities can be extended by adding new types.",
        concern="Extension points are not explicitly called out — it's unclear what would change if requirements grew.",
        suggestion="Identify the top 2 likely extensions (e.g., new payment method, new vehicle type) and explain how your design handles them without modification.",
        confidence="medium",
        display_order=5,
    ),
    RubricCriterion(
        name="Edge Cases & Testability",
        score=5.5,
        evidence="Some edge cases mentioned (e.g., full capacity, invalid input).",
        concern="Not all failure paths are addressed. Testability is not explicitly discussed.",
        suggestion="Add edge cases for concurrent access, boundary conditions, and error propagation. Describe how you would unit test the core logic.",
        confidence="medium",
        display_order=6,
    ),
    RubricCriterion(
        name="Design Explanation",
        score=7.0,
        evidence="A design explanation is present and covers the main decisions.",
        concern="Trade-offs and alternatives considered are not discussed.",
        suggestion="Explain why you chose this structure over alternatives. What would you do differently with more time?",
        confidence="high",
        display_order=7,
    ),
]


class MockEvaluator(BaseEvaluator):
    """
    Returns realistic but fixed mock feedback.
    Never used to present as 'AI feedback'.
    """

    @property
    def evaluator_type(self) -> str:
        return "mock"

    def evaluate(self, problem: Problem, submission: Submission) -> Evaluation:
        now = datetime.now(timezone.utc)
        overall = round(sum(c.score for c in _MOCK_CRITERIA) / len(_MOCK_CRITERIA) * 10, 1)
        return Evaluation(
            id=self._make_evaluation_id(),
            attempt_id=submission.attempt_id,
            status="completed",
            evaluator_type=self.evaluator_type,
            overall_score=overall,
            summary=(
                "This is a mock evaluation used when AI evaluation is unavailable. "
                "The scores are illustrative. Submit with AI enabled for real feedback."
            ),
            strengths=[
                "Core entities are identified",
                "A design explanation is provided",
                "Some edge cases are considered",
            ],
            improvements=[
                "Add explicit interfaces for key abstractions",
                "Name and justify design patterns used",
                "Expand edge case coverage to include concurrent access",
            ],
            criteria=list(_MOCK_CRITERIA),
            is_fallback=True,
            created_at=now,
            completed_at=now,
        )
