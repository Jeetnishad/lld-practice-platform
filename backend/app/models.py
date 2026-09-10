"""
SQLAlchemy ORM models — the persistence layer.
Domain objects live in app/domain/; these models handle DB mapping.
"""
import uuid
from datetime import datetime, timezone

from app.extensions import db


def _now():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class ProblemModel(db.Model):
    __tablename__ = "problems"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)  # easy | medium | hard
    short_description = db.Column(db.Text, nullable=False)
    detailed_requirements = db.Column(db.Text, nullable=False)
    assumptions = db.Column(db.Text, nullable=False)
    submission_guidance = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_now)

    attempts = db.relationship("AttemptModel", back_populates="problem", lazy="dynamic")

    def __repr__(self):
        return f"<Problem {self.slug}>"


class AttemptModel(db.Model):
    __tablename__ = "attempts"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    problem_id = db.Column(db.String(36), db.ForeignKey("problems.id"), nullable=False, index=True)
    learner_id = db.Column(db.String(100), nullable=False, default="demo-learner")
    attempt_number = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="in_progress")
    # status: in_progress | submitted | evaluating | completed | failed
    created_at = db.Column(db.DateTime, default=_now)
    updated_at = db.Column(db.DateTime, default=_now, onupdate=_now)

    problem = db.relationship("ProblemModel", back_populates="attempts")
    submission = db.relationship("SubmissionModel", back_populates="attempt", uselist=False)
    evaluation = db.relationship("EvaluationModel", back_populates="attempt", uselist=False)

    def __repr__(self):
        return f"<Attempt {self.id} problem={self.problem_id}>"


class SubmissionModel(db.Model):
    __tablename__ = "submissions"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    attempt_id = db.Column(db.String(36), db.ForeignKey("attempts.id"), unique=True, nullable=False, index=True)
    submission_type = db.Column(db.String(50), nullable=False, default="structured_text")
    # assumptions, classes_json, interfaces, relationships, design_explanation, edge_cases
    assumptions = db.Column(db.Text, nullable=True)
    classes_json = db.Column(db.Text, nullable=False)  # JSON array of ClassEntry
    interfaces = db.Column(db.Text, nullable=True)
    relationships = db.Column(db.Text, nullable=True)
    design_explanation = db.Column(db.Text, nullable=True)
    edge_cases = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=_now)

    attempt = db.relationship("AttemptModel", back_populates="submission")

    def __repr__(self):
        return f"<Submission {self.id} attempt={self.attempt_id}>"


class EvaluationModel(db.Model):
    __tablename__ = "evaluations"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    attempt_id = db.Column(db.String(36), db.ForeignKey("attempts.id"), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="pending")
    # status: pending | evaluating | completed | failed
    evaluator_type = db.Column(db.String(50), nullable=True)
    overall_score = db.Column(db.Float, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    strengths_json = db.Column(db.Text, nullable=True)   # JSON array
    improvements_json = db.Column(db.Text, nullable=True)  # JSON array
    error_message = db.Column(db.Text, nullable=True)
    is_fallback = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=_now)
    completed_at = db.Column(db.DateTime, nullable=True)

    attempt = db.relationship("AttemptModel", back_populates="evaluation")
    criteria = db.relationship("FeedbackCriterionModel", back_populates="evaluation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Evaluation {self.id} status={self.status}>"


class FeedbackCriterionModel(db.Model):
    __tablename__ = "feedback_criteria"

    id = db.Column(db.String(36), primary_key=True, default=_uuid)
    evaluation_id = db.Column(db.String(36), db.ForeignKey("evaluations.id"), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=10.0)
    evidence = db.Column(db.Text, nullable=True)
    concern = db.Column(db.Text, nullable=True)
    suggestion = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.String(20), nullable=True)  # low | medium | high
    display_order = db.Column(db.Integer, default=0)

    evaluation = db.relationship("EvaluationModel", back_populates="criteria")

    def __repr__(self):
        return f"<FeedbackCriterion {self.name} score={self.score}>"
