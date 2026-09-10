"""
RuleBasedEvaluator — deterministic evaluation using heuristic rules.

Does NOT use AI. Produces explainable feedback by inspecting the submission
structure: class count, method count, keyword presence, section completeness.

This evaluator is the default fallback when AI is unavailable and is also
useful for fast pre-screening before AI evaluation.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import List, Tuple

from app.domain.entities import Evaluation, Problem, RubricCriterion, Submission
from app.evaluators.base import BaseEvaluator


class RuleBasedEvaluator(BaseEvaluator):
    """
    Applies deterministic rules to score submissions.
    Fully transparent — the scoring logic is readable in this file.
    """

    @property
    def evaluator_type(self) -> str:
        return "rule_based"

    def evaluate(self, problem: Problem, submission: Submission) -> Evaluation:
        now = datetime.now(timezone.utc)
        criteria = [
            self._score_requirement_understanding(submission),
            self._score_class_responsibilities(submission),
            self._score_encapsulation(submission),
            self._score_coupling_cohesion(submission),
            self._score_abstraction_patterns(submission),
            self._score_extensibility(submission),
            self._score_edge_cases(submission),
            self._score_design_explanation(submission),
        ]

        total = sum(c.score for c in criteria)
        overall = round(total / len(criteria) * 10, 1)

        strengths, improvements = self._derive_strengths_improvements(criteria)

        return Evaluation(
            id=self._make_evaluation_id(),
            attempt_id=submission.attempt_id,
            status="completed",
            evaluator_type=self.evaluator_type,
            overall_score=overall,
            summary=self._build_summary(overall, criteria),
            strengths=strengths,
            improvements=improvements,
            criteria=criteria,
            is_fallback=True,
            created_at=now,
            completed_at=now,
        )

    # ------------------------------------------------------------------
    # Criterion scorers
    # ------------------------------------------------------------------

    def _score_requirement_understanding(self, sub: Submission) -> RubricCriterion:
        score = 5.0
        evidence_parts = []
        concern_parts = []
        suggestion_parts = []

        class_count = len(sub.classes)
        if class_count >= 5:
            score += 2.0
            evidence_parts.append(f"{class_count} classes identified, suggesting broad requirement coverage.")
        elif class_count >= 3:
            score += 1.0
            evidence_parts.append(f"{class_count} classes identified.")
        else:
            concern_parts.append(f"Only {class_count} class(es) — this may be too few to cover all requirements.")
            suggestion_parts.append("Re-read the requirements and ensure each major concept becomes a class or interface.")

        if sub.assumptions.strip():
            score += 1.0
            evidence_parts.append("Assumptions section is populated.")
        else:
            concern_parts.append("No assumptions stated.")
            suggestion_parts.append("State your assumptions explicitly — interviewers value this.")

        score = min(score, 10.0)
        return RubricCriterion(
            name="Requirement Understanding",
            score=round(score, 1),
            evidence=" ".join(evidence_parts) or "Basic requirements are partially addressed.",
            concern=" ".join(concern_parts) or "Some requirements may not be addressed.",
            suggestion=" ".join(suggestion_parts) or "Trace each requirement to at least one class.",
            confidence="high",
            display_order=0,
        )

    def _score_class_responsibilities(self, sub: Submission) -> RubricCriterion:
        score = 5.0
        evidence_parts = []
        concern_parts = []
        suggestion_parts = []

        classes_with_responsibility = [
            c for c in sub.classes if c.responsibility.strip()
        ]
        if len(classes_with_responsibility) == len(sub.classes) and sub.classes:
            score += 2.0
            evidence_parts.append("All classes have an explicit responsibility statement.")
        elif classes_with_responsibility:
            score += 1.0
            evidence_parts.append(f"{len(classes_with_responsibility)}/{len(sub.classes)} classes have responsibility statements.")
            concern_parts.append("Some classes lack a clear responsibility definition.")
            suggestion_parts.append("Ensure every class has a single, clear responsibility in one sentence.")

        # Check for god-class smell: one class with many methods
        for cls in sub.classes:
            if len(cls.methods) >= 8:
                score -= 1.0
                concern_parts.append(f"'{cls.name}' has {len(cls.methods)} methods — risk of god-class anti-pattern.")
                suggestion_parts.append(f"Consider splitting '{cls.name}' into focused sub-classes.")
                break

        score = max(1.0, min(score, 10.0))
        return RubricCriterion(
            name="Class Responsibilities",
            score=round(score, 1),
            evidence=" ".join(evidence_parts) or "Class responsibilities are partially defined.",
            concern=" ".join(concern_parts) or "Some responsibilities may overlap.",
            suggestion=" ".join(suggestion_parts) or "Apply SRP: each class should have one reason to change.",
            confidence="high",
            display_order=1,
        )

    def _score_encapsulation(self, sub: Submission) -> RubricCriterion:
        score = 4.0
        text = sub.interfaces.lower() + " " + sub.design_explanation.lower()
        keywords = ["interface", "abstract", "encapsulat", "private", "getter", "setter", "accessor"]
        matched = [k for k in keywords if k in text]

        if len(matched) >= 3:
            score += 3.0
        elif len(matched) >= 1:
            score += 1.5

        if sub.interfaces.strip():
            score += 2.0

        score = min(score, 10.0)
        has_interfaces = bool(sub.interfaces.strip())
        return RubricCriterion(
            name="Encapsulation & Interfaces",
            score=round(score, 1),
            evidence=(
                f"Interfaces section {'populated' if has_interfaces else 'empty'}. "
                f"Encapsulation keywords found: {matched or 'none'}."
            ),
            concern=(
                "" if has_interfaces
                else "No interfaces defined — this limits abstraction and testability."
            ),
            suggestion=(
                "Define at least one interface (e.g., PaymentProcessor, VehicleRepository) "
                "and describe what it abstracts."
            ),
            confidence="medium",
            display_order=2,
        )

    def _score_coupling_cohesion(self, sub: Submission) -> RubricCriterion:
        score = 5.0
        text = (sub.relationships + " " + sub.design_explanation).lower()
        good_keywords = ["dependency injection", "di ", "composition", "inject", "decouple", "loose coupling"]
        bad_keywords = ["singleton", "global", "static", "hardcoded"]
        good_found = [k for k in good_keywords if k in text]
        bad_found = [k for k in bad_keywords if k in text]

        score += len(good_found) * 1.0
        score -= len(bad_found) * 0.75

        if sub.relationships.strip():
            score += 1.0

        score = max(1.0, min(score, 10.0))
        return RubricCriterion(
            name="Coupling & Cohesion",
            score=round(score, 1),
            evidence=(
                f"Good coupling practices mentioned: {good_found or 'none'}. "
                f"Potentially tight coupling indicators: {bad_found or 'none'}."
            ),
            concern=(
                f"Found coupling red flags: {bad_found}." if bad_found
                else "Coupling strategy is not explicitly described."
            ),
            suggestion=(
                "Use dependency injection for services. "
                "Avoid singletons for stateful components. "
                "Group related methods into cohesive classes."
            ),
            confidence="medium",
            display_order=3,
        )

    def _score_abstraction_patterns(self, sub: Submission) -> RubricCriterion:
        score = 4.0
        all_text = " ".join([
            sub.design_explanation,
            sub.interfaces,
            " ".join(c.notes for c in sub.classes),
        ]).lower()

        pattern_keywords = [
            "factory", "strategy", "observer", "decorator", "command",
            "template method", "state pattern", "facade", "adapter",
            "repository", "singleton", "builder", "composite",
        ]
        found_patterns = [p for p in pattern_keywords if p in all_text]

        if len(found_patterns) >= 2:
            score += 3.0
        elif len(found_patterns) == 1:
            score += 1.5

        abstract_keywords = ["abstract", "polymorphi", "inherit", "overrid", "extends", "implements"]
        abstract_found = [k for k in abstract_keywords if k in all_text]
        score += min(len(abstract_found) * 0.5, 2.0)

        score = min(score, 10.0)
        return RubricCriterion(
            name="Abstraction / Design Patterns",
            score=round(score, 1),
            evidence=(
                f"Design patterns mentioned: {found_patterns or 'none'}. "
                f"Abstraction keywords: {abstract_found or 'none'}."
            ),
            concern=(
                "No design patterns explicitly named or justified."
                if not found_patterns
                else "Patterns mentioned but not all justified with reasoning."
            ),
            suggestion=(
                "Identify 1–2 patterns that fit this domain (e.g., Strategy for pricing, "
                "Observer for state changes) and explain why you chose them."
            ),
            confidence="medium",
            display_order=4,
        )

    def _score_extensibility(self, sub: Submission) -> RubricCriterion:
        score = 4.0
        all_text = (sub.design_explanation + " " + sub.interfaces).lower()
        keywords = [
            "extend", "plugin", "open/closed", "ocp", "new type", "future",
            "can be added", "without modifying", "without changing",
        ]
        found = [k for k in keywords if k in all_text]
        score += min(len(found) * 1.5, 4.0)

        class_methods_total = sum(len(c.methods) for c in sub.classes)
        if class_methods_total >= 10:
            score += 1.0

        score = min(score, 10.0)
        return RubricCriterion(
            name="Extensibility",
            score=round(score, 1),
            evidence=(
                f"Extensibility concepts present: {found or 'none'}. "
                f"Total methods across classes: {class_methods_total}."
            ),
            concern=(
                "Extension strategy is not explicitly described."
                if not found
                else "Some extension points are mentioned but not fully elaborated."
            ),
            suggestion=(
                "Describe the top 2 likely extensions and show they can be implemented "
                "without modifying existing classes (Open/Closed Principle)."
            ),
            confidence="medium",
            display_order=5,
        )

    def _score_edge_cases(self, sub: Submission) -> RubricCriterion:
        score = 4.0
        text = sub.edge_cases.lower() + " " + sub.design_explanation.lower()
        edge_keywords = [
            "concurrent", "null", "empty", "overflow", "full", "invalid",
            "timeout", "duplicate", "race condition", "negative", "max",
            "min", "boundary", "error", "exception", "fail",
        ]
        found = [k for k in edge_keywords if k in text]
        score += min(len(found) * 0.75, 4.0)

        if sub.edge_cases.strip():
            score += 1.5

        score = min(score, 10.0)
        return RubricCriterion(
            name="Edge Cases & Testability",
            score=round(score, 1),
            evidence=(
                f"Edge case keywords found: {found[:5] or 'none'}. "
                f"Edge cases section {'populated' if sub.edge_cases.strip() else 'empty'}."
            ),
            concern=(
                "No edge cases section provided."
                if not sub.edge_cases.strip()
                else "Some common edge cases (concurrent access, boundary conditions) may be missing."
            ),
            suggestion=(
                "Cover: full capacity, concurrent requests, invalid input, "
                "timeout/retry, boundary conditions, and null states."
            ),
            confidence="high",
            display_order=6,
        )

    def _score_design_explanation(self, sub: Submission) -> RubricCriterion:
        score = 3.0
        explanation = sub.design_explanation.strip()
        word_count = len(explanation.split()) if explanation else 0

        if word_count >= 100:
            score += 4.0
        elif word_count >= 50:
            score += 2.5
        elif word_count >= 20:
            score += 1.0

        tradeoff_keywords = ["trade-off", "tradeoff", "alternative", "chose", "decided", "instead of", "over"]
        tradeoffs_found = [k for k in tradeoff_keywords if k in explanation.lower()]
        if tradeoffs_found:
            score += 2.0

        score = min(score, 10.0)
        return RubricCriterion(
            name="Design Explanation",
            score=round(score, 1),
            evidence=(
                f"Design explanation: {word_count} words. "
                f"Trade-off discussion: {'present' if tradeoffs_found else 'absent'}."
            ),
            concern=(
                "Design explanation is very brief or missing."
                if word_count < 30
                else "Trade-off analysis and alternatives considered are not discussed."
                if not tradeoffs_found
                else ""
            ),
            suggestion=(
                "Write a paragraph (80+ words) explaining your key design decisions, "
                "what alternatives you considered, and what you would change with more time."
            ),
            confidence="high",
            display_order=7,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _derive_strengths_improvements(
        self, criteria: List[RubricCriterion]
    ) -> Tuple[List[str], List[str]]:
        sorted_by_score = sorted(criteria, key=lambda c: c.score, reverse=True)
        strengths = [
            f"{c.name} ({c.score}/10): {c.evidence[:100]}"
            for c in sorted_by_score[:3] if c.score >= 6
        ]
        improvements = [
            f"{c.name}: {c.suggestion[:120]}"
            for c in sorted_by_score[-3:] if c.score < 7
        ]
        return strengths, improvements

    def _build_summary(self, overall: float, criteria: List[RubricCriterion]) -> str:
        if overall >= 80:
            quality = "strong"
        elif overall >= 60:
            quality = "solid"
        elif overall >= 40:
            quality = "developing"
        else:
            quality = "needs significant work"

        weakest = min(criteria, key=lambda c: c.score)
        return (
            f"This is a {quality} LLD submission with an overall score of {overall}/100. "
            f"The weakest area is '{weakest.name}' ({weakest.score}/10). "
            f"Rule-based evaluation is applied — enable AI evaluation for deeper qualitative feedback."
        )
