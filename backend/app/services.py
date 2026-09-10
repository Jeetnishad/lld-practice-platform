"""
Application Service Layer — orchestrates the practice workflow.

This is the only place that coordinates:
  - Repositories (data access)
  - Evaluators (feedback generation)
  - Domain rules (business logic)

The Flask API calls this service. The service never imports Flask.
"""
from __future__ import annotations

import logging
import threading
from typing import List, Optional

from app.config import Config
from app.domain.entities import Attempt, Evaluation, Problem, Submission
from app.evaluators.base import BaseEvaluator
from app.evaluators.factory import get_evaluator
from app.repositories import (
    AttemptRepository,
    EvaluationRepository,
    ProblemRepository,
    SubmissionRepository,
)

logger = logging.getLogger(__name__)


class DuplicateSubmissionError(ValueError):
    """Raised when a submission already exists for an attempt."""
    pass


class PracticeService:
    """
    Orchestrates the complete LLD practice workflow:
    Problem → Attempt → Submission → Evaluation → Feedback
    """

    def __init__(
        self,
        problem_repo: ProblemRepository,
        attempt_repo: AttemptRepository,
        submission_repo: SubmissionRepository,
        evaluation_repo: EvaluationRepository,
        evaluator: BaseEvaluator,
    ):
        self._problems = problem_repo
        self._attempts = attempt_repo
        self._submissions = submission_repo
        self._evaluations = evaluation_repo
        self._evaluator = evaluator

    # ------------------------------------------------------------------
    # Problems
    # ------------------------------------------------------------------

    def get_all_problems(self) -> List[Problem]:
        return self._problems.get_all()

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        return self._problems.get_by_id(problem_id)

    def get_problem_by_slug(self, slug: str) -> Optional[Problem]:
        return self._problems.get_by_slug(slug)

    # ------------------------------------------------------------------
    # Attempts
    # ------------------------------------------------------------------

    def start_attempt(self, problem_id: str, learner_id: str = "demo-learner") -> Attempt:
        problem = self._problems.get_by_id(problem_id)
        if not problem:
            raise ValueError(f"Problem {problem_id} not found")
        return self._attempts.create(problem_id, learner_id)

    def get_attempt(self, attempt_id: str) -> Optional[Attempt]:
        return self._attempts.get_by_id(attempt_id)

    def get_all_attempts(self, learner_id: str = "demo-learner") -> List[Attempt]:
        return self._attempts.get_all(learner_id)

    def delete_attempt(self, attempt_id: str) -> None:
        """Delete an attempt and all related data (submission, evaluation, criteria).
        Raises ValueError if the attempt does not exist."""
        found = self._attempts.delete(attempt_id)
        if not found:
            raise ValueError(f"Attempt {attempt_id} not found")

    # ------------------------------------------------------------------
    # Submissions
    # ------------------------------------------------------------------

    def submit_solution(self, attempt_id: str, submission_data: dict) -> Evaluation:
        """
        Persist submission → trigger evaluation (in background thread).
        Returns the Evaluation in PENDING/EVALUATING state immediately.
        Submission is always persisted before evaluation begins.
        """
        attempt = self._attempts.get_by_id(attempt_id)
        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")

        # Prevent duplicate submission — check FIRST, before status check
        existing_submission = self._submissions.get_by_attempt_id(attempt_id)
        if existing_submission:
            raise DuplicateSubmissionError("A submission already exists for this attempt.")

        if attempt.status not in ("in_progress",):
            raise ValueError(
                f"Attempt is in status '{attempt.status}'. Only 'in_progress' attempts can be submitted."
            )

        # Validate submission has content
        classes = submission_data.get("classes", [])
        explanation = submission_data.get("design_explanation", "").strip()
        if not classes and not explanation:
            raise ValueError("Submission must include at least one class or a design explanation.")

        # Persist submission FIRST (important: if evaluation fails, submission is safe)
        self._submissions.create(attempt_id, submission_data)
        self._attempts.update_status(attempt_id, "submitted")

        # Create evaluation record in pending state
        evaluation = self._evaluations.create_pending(attempt_id)

        # Start evaluation in background thread — capture app now, while in request context
        from flask import current_app
        flask_app = current_app._get_current_object()  # type: ignore
        self._run_evaluation_async(flask_app, attempt_id, evaluation.id)

        return evaluation

    def _run_evaluation_async(self, flask_app, attempt_id: str, evaluation_id: str) -> None:
        """Runs evaluation in a background thread. MVP approach — see DESIGN.md for scaling.
        
        flask_app is the actual app instance (not a proxy) captured on the request thread.
        """
        thread = threading.Thread(
            target=self._run_evaluation,
            args=(flask_app, attempt_id, evaluation_id),
            daemon=True,
        )
        thread.start()

    def _run_evaluation(self, flask_app, attempt_id: str, evaluation_id: str) -> None:
        """Perform evaluation; update DB with result or failure."""
        with flask_app.app_context():
            try:
                self._evaluations.mark_evaluating(evaluation_id)
                self._attempts.update_status(attempt_id, "evaluating")

                attempt = self._attempts.get_by_id(attempt_id)
                if not attempt or not attempt.submission or not attempt.problem:
                    raise ValueError("Attempt, submission or problem not found for evaluation")

                result = self._evaluator.evaluate(attempt.problem, attempt.submission)
                result.id = evaluation_id
                result.attempt_id = attempt_id

                if result.status == "failed":
                    self._evaluations.save_result(evaluation_id, result)
                    self._attempts.update_status(attempt_id, "failed")
                else:
                    self._evaluations.save_result(evaluation_id, result)
                    self._attempts.update_status(attempt_id, "completed")

            except Exception as exc:
                logger.error("Evaluation failed for attempt %s: %s", attempt_id, exc, exc_info=True)
                try:
                    from app.domain.entities import Evaluation
                    from datetime import datetime, timezone
                    failed_eval = Evaluation(
                        id=evaluation_id,
                        attempt_id=attempt_id,
                        status="failed",
                        evaluator_type="unknown",
                        overall_score=None,
                        summary="",
                        strengths=[],
                        improvements=[],
                        criteria=[],
                        error_message=str(exc),
                    )
                    self._evaluations.save_result(evaluation_id, failed_eval)
                    self._attempts.update_status(attempt_id, "failed")
                except Exception as inner:
                    logger.error("Failed to persist evaluation failure: %s", inner)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def get_evaluation(self, attempt_id: str) -> Optional[Evaluation]:
        return self._evaluations.get_by_attempt_id(attempt_id)

    def retry_evaluation(self, attempt_id: str) -> Evaluation:
        """Retry a failed evaluation. Requires existing submission and failed status."""
        attempt = self._attempts.get_by_id(attempt_id)
        if not attempt:
            raise ValueError(f"Attempt {attempt_id} not found")

        if attempt.status != "failed":
            raise ValueError(
                f"Can only retry failed attempts. Current status: '{attempt.status}'"
            )

        if not attempt.submission:
            raise ValueError("No submission found. Cannot retry without a submission.")

        # Reuse existing evaluation record or create new one
        existing_eval = self._evaluations.get_by_attempt_id(attempt_id)
        if existing_eval:
            evaluation_id = existing_eval.id
            self._evaluations.mark_evaluating(evaluation_id)
        else:
            new_eval = self._evaluations.create_pending(attempt_id)
            evaluation_id = new_eval.id

        self._attempts.update_status(attempt_id, "evaluating")

        from flask import current_app
        flask_app = current_app._get_current_object()  # type: ignore
        self._run_evaluation_async(flask_app, attempt_id, evaluation_id)

        return self._evaluations.get_by_id(evaluation_id)


# ---------------------------------------------------------------------------
# Service factory — called once during app creation
# ---------------------------------------------------------------------------

def create_practice_service(config: Config) -> PracticeService:
    evaluator = get_evaluator(config)
    return PracticeService(
        problem_repo=ProblemRepository(),
        attempt_repo=AttemptRepository(),
        submission_repo=SubmissionRepository(),
        evaluation_repo=EvaluationRepository(),
        evaluator=evaluator,
    )
