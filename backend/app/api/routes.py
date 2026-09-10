"""
Flask API routes — thin layer that delegates to PracticeService.
All validation is done by Pydantic schemas before reaching the service.
"""
from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request
from pydantic import ValidationError

from app.schemas import (
    StartAttemptRequest,
    SubmissionRequest,
    err,
    ok,
    serialize_attempt,
    serialize_evaluation,
    serialize_problem,
)
from app.services import DuplicateSubmissionError

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


def _service():
    return current_app.practice_service


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "lld-practice-platform"}), 200


# ---------------------------------------------------------------------------
# Problems
# ---------------------------------------------------------------------------

@api_bp.route("/problems", methods=["GET"])
def list_problems():
    problems = _service().get_all_problems()
    return jsonify(ok([serialize_problem(p) for p in problems])), 200


@api_bp.route("/problems/<problem_id>", methods=["GET"])
def get_problem(problem_id: str):
    problem = _service().get_problem(problem_id)
    if not problem:
        # try by slug
        problem = _service().get_problem_by_slug(problem_id)
    if not problem:
        return jsonify(err(f"Problem '{problem_id}' not found")), 404
    return jsonify(ok(serialize_problem(problem))), 200


# ---------------------------------------------------------------------------
# Attempts
# ---------------------------------------------------------------------------

@api_bp.route("/attempts", methods=["GET"])
def list_attempts():
    learner_id = request.args.get("learner_id", "demo-learner")
    attempts = _service().get_all_attempts(learner_id)
    return jsonify(ok([serialize_attempt(a) for a in attempts])), 200


@api_bp.route("/attempts", methods=["POST"])
def create_attempt():
    try:
        body = StartAttemptRequest(**request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify(err(str(e))), 422
    except Exception:
        return jsonify(err("Invalid request body")), 400

    try:
        attempt = _service().start_attempt(body.problem_id, body.learner_id)
        return jsonify(ok(serialize_attempt(attempt), "Attempt started")), 201
    except ValueError as e:
        return jsonify(err(str(e))), 404


@api_bp.route("/attempts/<attempt_id>", methods=["GET"])
def get_attempt(attempt_id: str):
    attempt = _service().get_attempt(attempt_id)
    if not attempt:
        return jsonify(err(f"Attempt '{attempt_id}' not found")), 404
    return jsonify(ok(serialize_attempt(attempt))), 200


@api_bp.route("/attempts/<attempt_id>", methods=["DELETE"])
def delete_attempt(attempt_id: str):
    try:
        _service().delete_attempt(attempt_id)
        return "", 204
    except ValueError as e:
        return jsonify(err(str(e))), 404


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

@api_bp.route("/attempts/<attempt_id>/submissions", methods=["POST"])
def submit_solution(attempt_id: str):
    try:
        body = SubmissionRequest(**request.get_json(force=True) or {})
    except ValidationError as e:
        return jsonify(err(str(e))), 422
    except Exception:
        return jsonify(err("Invalid request body")), 400

    # Check total submission size
    total_text = " ".join([
        body.assumptions,
        body.interfaces,
        body.relationships,
        body.design_explanation,
        body.edge_cases,
        " ".join(c.name + c.responsibility for c in body.classes),
    ])
    max_size = current_app.config.get("MAX_SUBMISSION_SIZE", 50_000)
    if len(total_text) > max_size:
        return jsonify(err(f"Submission too large (max {max_size} characters)")), 422

    submission_data = {
        "assumptions": body.assumptions,
        "classes": [c.model_dump() for c in body.classes],
        "interfaces": body.interfaces,
        "relationships": body.relationships,
        "design_explanation": body.design_explanation,
        "edge_cases": body.edge_cases,
    }

    try:
        evaluation = _service().submit_solution(attempt_id, submission_data)
        return jsonify(ok(serialize_evaluation(evaluation), "Submitted. Evaluation in progress.")), 202
    except DuplicateSubmissionError as e:
        return jsonify(err(str(e))), 409
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return jsonify(err(msg)), 404
        return jsonify(err(msg)), 422


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

@api_bp.route("/attempts/<attempt_id>/evaluation", methods=["GET"])
def get_evaluation(attempt_id: str):
    evaluation = _service().get_evaluation(attempt_id)
    if not evaluation:
        return jsonify(err(f"No evaluation found for attempt '{attempt_id}'")), 404
    return jsonify(ok(serialize_evaluation(evaluation))), 200


@api_bp.route("/attempts/<attempt_id>/evaluation/retry", methods=["POST"])
def retry_evaluation(attempt_id: str):
    try:
        evaluation = _service().retry_evaluation(attempt_id)
        return jsonify(ok(serialize_evaluation(evaluation), "Retry started")), 202
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            return jsonify(err(msg)), 404
        return jsonify(err(msg)), 422


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@api_bp.errorhandler(404)
def not_found(e):
    return jsonify(err("Resource not found")), 404


@api_bp.errorhandler(405)
def method_not_allowed(e):
    return jsonify(err("Method not allowed")), 405


@api_bp.errorhandler(500)
def server_error(e):
    logger.error("Unhandled server error: %s", e, exc_info=True)
    return jsonify(err("Internal server error")), 500
