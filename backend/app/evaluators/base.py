"""
Evaluator abstraction — the core extensibility contract.

Any evaluator must implement: evaluate(problem, submission) -> Evaluation

Adding a new evaluator (HumanEvaluator, CodeEvaluator, etc.) requires:
  1. Subclass BaseEvaluator
  2. Implement evaluate()
  3. Register in evaluator_factory.py

The practice workflow never changes.
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities import Evaluation, Problem, Submission

# Fixed rubric — applied consistently across all evaluator implementations
RUBRIC_CRITERIA = [
    "Requirement Understanding",
    "Class Responsibilities",
    "Encapsulation & Interfaces",
    "Coupling & Cohesion",
    "Abstraction / Design Patterns",
    "Extensibility",
    "Edge Cases & Testability",
    "Design Explanation",
]


class BaseEvaluator(ABC):
    """
    Abstract evaluator interface.
    Concrete implementations: MockEvaluator, RuleBasedEvaluator, AIEvaluator.
    """

    @property
    @abstractmethod
    def evaluator_type(self) -> str:
        """Human-readable name for this evaluator (stored in DB)."""
        ...

    @abstractmethod
    def evaluate(self, problem: "Problem", submission: "Submission") -> "Evaluation":
        """
        Evaluate a submission against a problem and return a full Evaluation.
        Must NOT raise on transient failures — return a failed Evaluation instead.
        """
        ...

    def _make_evaluation_id(self) -> str:
        return str(uuid.uuid4())

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)
