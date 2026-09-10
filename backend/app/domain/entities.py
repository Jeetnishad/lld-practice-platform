"""
Domain layer — pure Python dataclasses, no DB dependencies.
These represent the core business concepts of the LLD Practice Platform.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationStatus(str, Enum):
    PENDING = "pending"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ClassEntry:
    """A single class in a learner's LLD design."""
    name: str
    responsibility: str
    methods: List[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "methods": self.methods,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClassEntry":
        return cls(
            name=data.get("name", ""),
            responsibility=data.get("responsibility", ""),
            methods=data.get("methods", []),
            notes=data.get("notes", ""),
        )


@dataclass
class Submission:
    """
    A learner's structured text submission for an LLD problem.
    Designed to be extended: TextSubmission, CodeSubmission, DiagramSubmission.
    """
    id: str
    attempt_id: str
    submission_type: str
    assumptions: str
    classes: List[ClassEntry]
    interfaces: str
    relationships: str
    design_explanation: str
    edge_cases: str
    submitted_at: Optional[datetime] = None

    def to_text_summary(self) -> str:
        """Produce a readable text for AI evaluation."""
        lines = []
        if self.assumptions:
            lines.append(f"=== ASSUMPTIONS ===\n{self.assumptions}")
        lines.append("=== CLASSES ===")
        for cls in self.classes:
            lines.append(f"\nClass: {cls.name}")
            lines.append(f"Responsibility: {cls.responsibility}")
            if cls.methods:
                lines.append(f"Methods: {', '.join(cls.methods)}")
            if cls.notes:
                lines.append(f"Notes: {cls.notes}")
        if self.interfaces:
            lines.append(f"\n=== INTERFACES ===\n{self.interfaces}")
        if self.relationships:
            lines.append(f"\n=== RELATIONSHIPS ===\n{self.relationships}")
        if self.design_explanation:
            lines.append(f"\n=== DESIGN EXPLANATION ===\n{self.design_explanation}")
        if self.edge_cases:
            lines.append(f"\n=== EDGE CASES ===\n{self.edge_cases}")
        return "\n".join(lines)

    def is_empty(self) -> bool:
        return not self.classes and not self.design_explanation.strip()


@dataclass
class Problem:
    """An LLD problem to practice."""
    id: str
    slug: str
    title: str
    difficulty: str
    short_description: str
    detailed_requirements: str
    assumptions: str
    submission_guidance: str
    created_at: Optional[datetime] = None


@dataclass
class RubricCriterion:
    """A single evaluated rubric criterion with full explainability."""
    name: str
    score: float
    max_score: float = 10.0
    evidence: str = ""
    concern: str = ""
    suggestion: str = ""
    confidence: str = "medium"
    display_order: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": self.score,
            "max_score": self.max_score,
            "evidence": self.evidence,
            "concern": self.concern,
            "suggestion": self.suggestion,
            "confidence": self.confidence,
        }


@dataclass
class Evaluation:
    """
    The result of evaluating a Submission against the rubric.
    Contains explainable per-criterion feedback plus overall assessment.
    """
    id: str
    attempt_id: str
    status: str
    evaluator_type: str
    overall_score: Optional[float]
    summary: str
    strengths: List[str]
    improvements: List[str]
    criteria: List[RubricCriterion]
    is_fallback: bool = False
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def score_percentage(self) -> Optional[float]:
        if self.overall_score is None:
            return None
        return round(self.overall_score, 1)


@dataclass
class Attempt:
    """
    Represents a single practice attempt by a learner on a problem.
    One Attempt → one Submission → one Evaluation.
    """
    id: str
    problem_id: str
    learner_id: str
    attempt_number: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    problem: Optional[Problem] = None
    submission: Optional[Submission] = None
    evaluation: Optional[Evaluation] = None
