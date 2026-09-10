"""
AIEvaluator — evaluates submissions using OpenAI with structured JSON output.

Design decisions:
  - Calls OpenAI through a thin provider layer (can swap to Anthropic, Gemini, etc.)
  - Requires structured JSON response (validated with Pydantic)
  - Falls back gracefully on any failure — never crashes the app
  - API key comes ONLY from environment — never hardcoded
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError

from app.domain.entities import Evaluation, Problem, RubricCriterion, Submission
from app.evaluators.base import BaseEvaluator, RUBRIC_CRITERIA

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic models for validating AI response
# ---------------------------------------------------------------------------

class AICriterionResponse(BaseModel):
    name: str
    score: float = Field(ge=0, le=10)
    evidence: str = ""
    concern: str = ""
    suggestion: str = ""
    confidence: str = "medium"


class AIEvaluationResponse(BaseModel):
    criteria: List[AICriterionResponse]
    overall_score: float = Field(ge=0, le=100)
    summary: str = ""
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert software design reviewer specializing in Low-Level Design (LLD).
You evaluate LLD submissions from learners using a fixed rubric.
You provide specific, evidence-based feedback from the learner's own submission.
You are fair, constructive, and educational.
You MUST respond with valid JSON only — no markdown, no explanation outside JSON."""

def _build_evaluation_prompt(problem: Problem, submission: Submission) -> str:
    criteria_list = "\n".join(f"  - {c}" for c in RUBRIC_CRITERIA)
    return f"""Evaluate this LLD submission for the problem: "{problem.title}"

PROBLEM DESCRIPTION:
{problem.short_description}

DETAILED REQUIREMENTS:
{problem.detailed_requirements}

LEARNER'S SUBMISSION:
{submission.to_text_summary()}

RUBRIC CRITERIA (score each 0-10):
{criteria_list}

For each criterion provide:
- name: exact criterion name from the list
- score: 0-10 (float)
- evidence: quote or reference from the learner's submission
- concern: specific problem or gap identified
- suggestion: actionable improvement advice
- confidence: "low" | "medium" | "high"

Also provide:
- overall_score: weighted average * 10, so 0-100
- summary: 2-3 sentence overall assessment
- strengths: list of 2-4 specific strengths (strings)
- improvements: list of 2-4 specific improvements (strings)

Respond with ONLY this JSON structure:
{{
  "criteria": [...],
  "overall_score": <number>,
  "summary": "...",
  "strengths": [...],
  "improvements": [...]
}}"""


# ---------------------------------------------------------------------------
# AIEvaluator
# ---------------------------------------------------------------------------

class AIEvaluator(BaseEvaluator):
    """
    Evaluates submissions using OpenAI.
    Validates the response with Pydantic before accepting it.
    Falls back gracefully on any failure.
    """

    def __init__(self, api_key: str, model: str = "gpt-4o", timeout: int = 30):
        self._api_key = api_key
        self._model = model
        self._timeout = timeout

    @property
    def evaluator_type(self) -> str:
        return "ai"

    def evaluate(self, problem: Problem, submission: Submission) -> Evaluation:
        now = datetime.now(timezone.utc)
        try:
            raw = self._call_openai(problem, submission)
            parsed = self._parse_and_validate(raw)
            return self._build_evaluation(submission, parsed, now)
        except Exception as exc:
            logger.warning(
                "AIEvaluator failed (%s) — falling back to RuleBasedEvaluator", exc
            )
            return self._rule_based_fallback(problem, submission, original_error=str(exc))

    def _rule_based_fallback(
        self, problem: Problem, submission: Submission, original_error: str
    ) -> Evaluation:
        """
        Called when AIEvaluator fails at runtime.
        Delegates to RuleBasedEvaluator and marks the result as a fallback.
        If RuleBasedEvaluator also raises, returns a failed Evaluation.
        """
        from app.evaluators.rule_based_evaluator import RuleBasedEvaluator
        now = datetime.now(timezone.utc)
        try:
            fallback = RuleBasedEvaluator()
            result = fallback.evaluate(problem, submission)
            result.is_fallback = True
            return result
        except Exception as fallback_exc:
            logger.error(
                "RuleBasedEvaluator fallback also failed: %s", fallback_exc, exc_info=True
            )
            return Evaluation(
                id=self._make_evaluation_id(),
                attempt_id=submission.attempt_id,
                status="failed",
                evaluator_type=self.evaluator_type,
                overall_score=None,
                summary="",
                strengths=[],
                improvements=[],
                criteria=[],
                is_fallback=False,
                error_message=f"AI failed: {original_error}. Fallback also failed: {fallback_exc}",
                created_at=now,
                completed_at=now,
            )

    def _call_openai(self, problem: Problem, submission: Submission) -> str:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("openai package not installed") from e

        client = OpenAI(api_key=self._api_key, timeout=self._timeout)
        prompt = _build_evaluation_prompt(problem, submission)

        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")
        return content

    def _parse_and_validate(self, raw: str) -> AIEvaluationResponse:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {e}") from e

        try:
            return AIEvaluationResponse(**data)
        except ValidationError as e:
            raise ValueError(f"AI response failed validation: {e}") from e

    def _build_evaluation(
        self,
        submission: Submission,
        parsed: AIEvaluationResponse,
        now: datetime,
    ) -> Evaluation:
        criteria = []
        for order, ai_crit in enumerate(parsed.criteria):
            criteria.append(RubricCriterion(
                name=ai_crit.name,
                score=ai_crit.score,
                evidence=ai_crit.evidence,
                concern=ai_crit.concern,
                suggestion=ai_crit.suggestion,
                confidence=ai_crit.confidence,
                display_order=order,
            ))

        return Evaluation(
            id=self._make_evaluation_id(),
            attempt_id=submission.attempt_id,
            status="completed",
            evaluator_type=self.evaluator_type,
            overall_score=parsed.overall_score,
            summary=parsed.summary,
            strengths=parsed.strengths,
            improvements=parsed.improvements,
            criteria=criteria,
            is_fallback=False,
            created_at=now,
            completed_at=now,
        )
