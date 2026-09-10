"""
Pydantic schemas for API request validation and response serialization.
Keeps validation logic out of Flask routes.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request schemas (incoming data)
# ---------------------------------------------------------------------------

class ClassEntryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    responsibility: str = Field(default="", max_length=1000)
    methods: List[str] = Field(default_factory=list)
    notes: str = Field(default="", max_length=1000)

    @field_validator("methods")
    @classmethod
    def validate_methods(cls, v):
        return [m.strip() for m in v if m.strip()][:20]  # max 20 methods


class SubmissionRequest(BaseModel):
    assumptions: str = Field(default="", max_length=5000)
    classes: List[ClassEntryRequest] = Field(default_factory=list)
    interfaces: str = Field(default="", max_length=5000)
    relationships: str = Field(default="", max_length=5000)
    design_explanation: str = Field(default="", max_length=10000)
    edge_cases: str = Field(default="", max_length=5000)

    @field_validator("classes")
    @classmethod
    def validate_classes(cls, v):
        if len(v) > 30:
            raise ValueError("Maximum 30 classes allowed")
        return v


class StartAttemptRequest(BaseModel):
    problem_id: str = Field(..., min_length=1)
    learner_id: str = Field(default="demo-learner", max_length=100)


# ---------------------------------------------------------------------------
# Response serializers (domain → dict)
# ---------------------------------------------------------------------------

def serialize_problem(problem) -> dict:
    return {
        "id": problem.id,
        "slug": problem.slug,
        "title": problem.title,
        "difficulty": problem.difficulty,
        "short_description": problem.short_description,
        "detailed_requirements": problem.detailed_requirements,
        "assumptions": problem.assumptions,
        "submission_guidance": problem.submission_guidance,
        "created_at": problem.created_at.isoformat() if problem.created_at else None,
    }


def serialize_class_entry(cls_entry) -> dict:
    return {
        "name": cls_entry.name,
        "responsibility": cls_entry.responsibility,
        "methods": cls_entry.methods,
        "notes": cls_entry.notes,
    }


def serialize_submission(submission) -> dict:
    return {
        "id": submission.id,
        "attempt_id": submission.attempt_id,
        "submission_type": submission.submission_type,
        "assumptions": submission.assumptions,
        "classes": [serialize_class_entry(c) for c in submission.classes],
        "interfaces": submission.interfaces,
        "relationships": submission.relationships,
        "design_explanation": submission.design_explanation,
        "edge_cases": submission.edge_cases,
        "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
    }


def serialize_criterion(criterion) -> dict:
    return {
        "name": criterion.name,
        "score": criterion.score,
        "max_score": criterion.max_score,
        "evidence": criterion.evidence,
        "concern": criterion.concern,
        "suggestion": criterion.suggestion,
        "confidence": criterion.confidence,
    }


def serialize_evaluation(evaluation) -> dict:
    return {
        "id": evaluation.id,
        "attempt_id": evaluation.attempt_id,
        "status": evaluation.status,
        "evaluator_type": evaluation.evaluator_type,
        "overall_score": evaluation.overall_score,
        "summary": evaluation.summary,
        "strengths": evaluation.strengths,
        "improvements": evaluation.improvements,
        "criteria": [serialize_criterion(c) for c in evaluation.criteria],
        "is_fallback": evaluation.is_fallback,
        "error_message": evaluation.error_message,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        "completed_at": evaluation.completed_at.isoformat() if evaluation.completed_at else None,
    }


def serialize_attempt(attempt, include_evaluation: bool = True) -> dict:
    data = {
        "id": attempt.id,
        "problem_id": attempt.problem_id,
        "learner_id": attempt.learner_id,
        "attempt_number": attempt.attempt_number,
        "status": attempt.status,
        "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
        "updated_at": attempt.updated_at.isoformat() if attempt.updated_at else None,
        "problem": serialize_problem(attempt.problem) if attempt.problem else None,
        "submission": serialize_submission(attempt.submission) if attempt.submission else None,
    }
    if include_evaluation:
        data["evaluation"] = serialize_evaluation(attempt.evaluation) if attempt.evaluation else None
    return data


def ok(data=None, message: str = "ok") -> dict:
    return {"status": "ok", "message": message, "data": data}


def err(message: str) -> dict:
    return {"status": "error", "message": message, "data": None}
