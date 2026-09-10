"""
Repository layer — abstracts all database access.
The service layer uses these repositories and never touches DB models directly.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import List, Optional

from app.domain.entities import (
    Attempt,
    ClassEntry,
    Evaluation,
    EvaluationStatus,
    Problem,
    RubricCriterion,
    Submission,
)
from app.extensions import db
from app.models import (
    AttemptModel,
    EvaluationModel,
    FeedbackCriterionModel,
    ProblemModel,
    SubmissionModel,
)


def _now():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Mappers: ORM → Domain
# ---------------------------------------------------------------------------

def _map_problem(m: ProblemModel) -> Problem:
    return Problem(
        id=m.id,
        slug=m.slug,
        title=m.title,
        difficulty=m.difficulty,
        short_description=m.short_description,
        detailed_requirements=m.detailed_requirements,
        assumptions=m.assumptions,
        submission_guidance=m.submission_guidance,
        created_at=m.created_at,
    )


def _map_submission(m: SubmissionModel) -> Submission:
    try:
        classes_data = json.loads(m.classes_json or "[]")
    except (json.JSONDecodeError, TypeError):
        classes_data = []
    return Submission(
        id=m.id,
        attempt_id=m.attempt_id,
        submission_type=m.submission_type,
        assumptions=m.assumptions or "",
        classes=[ClassEntry.from_dict(c) for c in classes_data],
        interfaces=m.interfaces or "",
        relationships=m.relationships or "",
        design_explanation=m.design_explanation or "",
        edge_cases=m.edge_cases or "",
        submitted_at=m.submitted_at,
    )


def _map_criterion(m: FeedbackCriterionModel) -> RubricCriterion:
    return RubricCriterion(
        name=m.name,
        score=m.score,
        max_score=m.max_score,
        evidence=m.evidence or "",
        concern=m.concern or "",
        suggestion=m.suggestion or "",
        confidence=m.confidence or "medium",
        display_order=m.display_order,
    )


def _map_evaluation(m: EvaluationModel) -> Evaluation:
    try:
        strengths = json.loads(m.strengths_json or "[]")
    except (json.JSONDecodeError, TypeError):
        strengths = []
    try:
        improvements = json.loads(m.improvements_json or "[]")
    except (json.JSONDecodeError, TypeError):
        improvements = []
    criteria = sorted(
        [_map_criterion(c) for c in m.criteria],
        key=lambda x: x.display_order,
    )
    return Evaluation(
        id=m.id,
        attempt_id=m.attempt_id,
        status=m.status,
        evaluator_type=m.evaluator_type or "",
        overall_score=m.overall_score,
        summary=m.summary or "",
        strengths=strengths,
        improvements=improvements,
        criteria=criteria,
        is_fallback=m.is_fallback or False,
        error_message=m.error_message,
        created_at=m.created_at,
        completed_at=m.completed_at,
    )


def _map_attempt(m: AttemptModel, include_related: bool = True) -> Attempt:
    attempt = Attempt(
        id=m.id,
        problem_id=m.problem_id,
        learner_id=m.learner_id,
        attempt_number=m.attempt_number,
        status=m.status,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )
    if include_related:
        attempt.problem = _map_problem(m.problem) if m.problem else None
        attempt.submission = _map_submission(m.submission) if m.submission else None
        attempt.evaluation = _map_evaluation(m.evaluation) if m.evaluation else None
    return attempt


# ---------------------------------------------------------------------------
# Problem Repository
# ---------------------------------------------------------------------------

class ProblemRepository:

    def get_all(self) -> List[Problem]:
        models = ProblemModel.query.order_by(ProblemModel.created_at).all()
        return [_map_problem(m) for m in models]

    def get_by_id(self, problem_id: str) -> Optional[Problem]:
        m = db.session.get(ProblemModel, problem_id)
        return _map_problem(m) if m else None

    def get_by_slug(self, slug: str) -> Optional[Problem]:
        m = ProblemModel.query.filter_by(slug=slug).first()
        return _map_problem(m) if m else None


# ---------------------------------------------------------------------------
# Attempt Repository
# ---------------------------------------------------------------------------

class AttemptRepository:

    def create(self, problem_id: str, learner_id: str = "demo-learner") -> Attempt:
        # Calculate attempt_number for this problem/learner
        count = AttemptModel.query.filter_by(
            problem_id=problem_id, learner_id=learner_id
        ).count()
        model = AttemptModel(
            problem_id=problem_id,
            learner_id=learner_id,
            attempt_number=count + 1,
            status="in_progress",
        )
        db.session.add(model)
        db.session.commit()
        db.session.refresh(model)
        return _map_attempt(model)

    def get_by_id(self, attempt_id: str) -> Optional[Attempt]:
        m = db.session.get(AttemptModel, attempt_id)
        return _map_attempt(m) if m else None

    def get_all(self, learner_id: str = "demo-learner") -> List[Attempt]:
        models = (
            AttemptModel.query
            .filter_by(learner_id=learner_id)
            .order_by(AttemptModel.created_at.desc())
            .all()
        )
        return [_map_attempt(m) for m in models]

    def update_status(self, attempt_id: str, status: str) -> Optional[Attempt]:
        m = db.session.get(AttemptModel, attempt_id)
        if not m:
            return None
        m.status = status
        m.updated_at = _now()
        db.session.commit()
        db.session.refresh(m)
        return _map_attempt(m)

    def delete(self, attempt_id: str) -> bool:
        """Delete an attempt and all its related rows (submission, evaluation, criteria).
        Returns True if found and deleted, False if not found."""
        m = db.session.get(AttemptModel, attempt_id)
        if not m:
            return False
        # Cascade: EvaluationModel has cascade="all, delete-orphan" on criteria.
        # We delete evaluation first (if present) so FK constraints are satisfied,
        # then submission, then the attempt itself.
        if m.evaluation:
            db.session.delete(m.evaluation)
        if m.submission:
            db.session.delete(m.submission)
        db.session.delete(m)
        db.session.commit()
        return True


# ---------------------------------------------------------------------------
# Submission Repository
# ---------------------------------------------------------------------------

class SubmissionRepository:

    def create(self, attempt_id: str, data: dict) -> Submission:
        classes = data.get("classes", [])
        model = SubmissionModel(
            attempt_id=attempt_id,
            submission_type=data.get("submission_type", "structured_text"),
            assumptions=data.get("assumptions", ""),
            classes_json=json.dumps([c if isinstance(c, dict) else c.to_dict() for c in classes]),
            interfaces=data.get("interfaces", ""),
            relationships=data.get("relationships", ""),
            design_explanation=data.get("design_explanation", ""),
            edge_cases=data.get("edge_cases", ""),
        )
        db.session.add(model)
        db.session.commit()
        db.session.refresh(model)
        return _map_submission(model)

    def get_by_attempt_id(self, attempt_id: str) -> Optional[Submission]:
        m = SubmissionModel.query.filter_by(attempt_id=attempt_id).first()
        return _map_submission(m) if m else None


# ---------------------------------------------------------------------------
# Evaluation Repository
# ---------------------------------------------------------------------------

class EvaluationRepository:

    def create_pending(self, attempt_id: str) -> Evaluation:
        model = EvaluationModel(
            attempt_id=attempt_id,
            status="pending",
        )
        db.session.add(model)
        db.session.commit()
        db.session.refresh(model)
        return _map_evaluation(model)

    def mark_evaluating(self, evaluation_id: str) -> Optional[Evaluation]:
        m = db.session.get(EvaluationModel, evaluation_id)
        if not m:
            return None
        m.status = "evaluating"
        db.session.commit()
        return _map_evaluation(m)

    def save_result(self, evaluation_id: str, result: Evaluation) -> Evaluation:
        m = db.session.get(EvaluationModel, evaluation_id)
        if not m:
            raise ValueError(f"Evaluation {evaluation_id} not found")
        m.status = result.status
        m.evaluator_type = result.evaluator_type
        m.overall_score = result.overall_score
        m.summary = result.summary
        m.strengths_json = json.dumps(result.strengths)
        m.improvements_json = json.dumps(result.improvements)
        m.is_fallback = result.is_fallback
        m.error_message = result.error_message
        m.completed_at = _now()
        # Remove old criteria and insert new
        FeedbackCriterionModel.query.filter_by(evaluation_id=evaluation_id).delete()
        for order, crit in enumerate(result.criteria):
            fc = FeedbackCriterionModel(
                evaluation_id=evaluation_id,
                name=crit.name,
                score=crit.score,
                max_score=crit.max_score,
                evidence=crit.evidence,
                concern=crit.concern,
                suggestion=crit.suggestion,
                confidence=crit.confidence,
                display_order=order,
            )
            db.session.add(fc)
        db.session.commit()
        db.session.refresh(m)
        return _map_evaluation(m)

    def get_by_attempt_id(self, attempt_id: str) -> Optional[Evaluation]:
        m = EvaluationModel.query.filter_by(attempt_id=attempt_id).first()
        return _map_evaluation(m) if m else None

    def get_by_id(self, evaluation_id: str) -> Optional[Evaluation]:
        m = db.session.get(EvaluationModel, evaluation_id)
        return _map_evaluation(m) if m else None
