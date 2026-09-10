"""
Tests for evaluator abstraction, MockEvaluator, RuleBasedEvaluator, and AI output validation.
"""
import pytest

from app.domain.entities import ClassEntry, Problem, Submission
from app.evaluators.mock_evaluator import MockEvaluator
from app.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.evaluators.base import BaseEvaluator, RUBRIC_CRITERIA
from app.evaluators.ai_evaluator import AIEvaluationResponse, AICriterionResponse
from pydantic import ValidationError


def make_problem():
    return Problem(
        id="test-prob-1",
        slug="parking-lot",
        title="Parking Lot",
        difficulty="medium",
        short_description="Design a parking lot.",
        detailed_requirements="Manage vehicle entry, exit, payment.",
        assumptions="Single lot.",
        submission_guidance="Include ParkingLot, Ticket classes.",
    )


def make_rich_submission():
    return Submission(
        id="test-sub-1",
        attempt_id="test-att-1",
        submission_type="structured_text",
        assumptions="Single lot, flat-rate pricing. Nearest spot assignment.",
        classes=[
            ClassEntry("ParkingLot", "Manages floors and occupancy", ["enterVehicle", "exitVehicle"], "Top-level facade"),
            ClassEntry("ParkingFloor", "Manages spots on a floor", ["getAvailableSpot", "markOccupied"], ""),
            ClassEntry("ParkingSpot", "Represents a single spot", ["isAvailable", "occupy", "free"], ""),
            ClassEntry("Ticket", "Holds entry time for fee calc", ["getEntryTime", "calculateFee"], ""),
            ClassEntry("PaymentProcessor", "Interface for payment", ["processPayment"], "Strategy interface"),
        ],
        interfaces="PaymentProcessor: processPayment(amount) -> Receipt\nSpotAssignmentStrategy: findSpot() -> Spot",
        relationships="ParkingLot has-many ParkingFloor. ParkingFloor has-many ParkingSpot.",
        design_explanation=(
            "I separated payment into a Strategy interface allowing Cash, Card, UPI without modifying core flow. "
            "SpotAssignmentStrategy enables different allocation algorithms. Trade-off: slightly more complex "
            "class hierarchy but much better extensibility and testability via dependency injection."
        ),
        edge_cases="Lot full: reject entry, concurrent access: floor-level lock, invalid ticket: reject exit.",
    )


def make_minimal_submission():
    return Submission(
        id="test-sub-2",
        attempt_id="test-att-2",
        submission_type="structured_text",
        assumptions="",
        classes=[ClassEntry("ParkingLot", "", [], "")],
        interfaces="",
        relationships="",
        design_explanation="A basic design.",
        edge_cases="",
    )


class TestEvaluatorAbstraction:

    def test_mock_evaluator_is_base_evaluator(self):
        """MockEvaluator must implement BaseEvaluator interface."""
        assert isinstance(MockEvaluator(), BaseEvaluator)

    def test_rule_based_evaluator_is_base_evaluator(self):
        """RuleBasedEvaluator must implement BaseEvaluator interface."""
        assert isinstance(RuleBasedEvaluator(), BaseEvaluator)

    def test_evaluator_type_property(self):
        assert MockEvaluator().evaluator_type == "mock"
        assert RuleBasedEvaluator().evaluator_type == "rule_based"

    def test_rubric_has_eight_criteria(self):
        assert len(RUBRIC_CRITERIA) == 8

    def test_swap_evaluator_same_interface(self):
        """Both evaluators should return the same Evaluation structure."""
        problem = make_problem()
        submission = make_rich_submission()
        for evaluator in [MockEvaluator(), RuleBasedEvaluator()]:
            result = evaluator.evaluate(problem, submission)
            assert result.status == "completed"
            assert result.overall_score is not None
            assert isinstance(result.criteria, list)
            assert isinstance(result.strengths, list)
            assert isinstance(result.improvements, list)


class TestMockEvaluator:

    def test_mock_evaluator_returns_completed(self):
        ev = MockEvaluator().evaluate(make_problem(), make_rich_submission())
        assert ev.status == "completed"

    def test_mock_evaluator_returns_8_criteria(self):
        ev = MockEvaluator().evaluate(make_problem(), make_rich_submission())
        assert len(ev.criteria) == 8

    def test_mock_evaluator_is_fallback(self):
        ev = MockEvaluator().evaluate(make_problem(), make_rich_submission())
        assert ev.is_fallback is True

    def test_mock_evaluator_has_overall_score(self):
        ev = MockEvaluator().evaluate(make_problem(), make_rich_submission())
        assert 0 <= ev.overall_score <= 100

    def test_mock_criteria_have_all_fields(self):
        ev = MockEvaluator().evaluate(make_problem(), make_rich_submission())
        for crit in ev.criteria:
            assert crit.name
            assert crit.evidence
            assert crit.suggestion
            assert crit.confidence in ("low", "medium", "high")


class TestRuleBasedEvaluator:

    def test_rich_submission_scores_higher_than_minimal(self):
        evaluator = RuleBasedEvaluator()
        problem = make_problem()
        rich_ev = evaluator.evaluate(problem, make_rich_submission())
        minimal_ev = evaluator.evaluate(problem, make_minimal_submission())
        assert rich_ev.overall_score > minimal_ev.overall_score

    def test_returns_8_criteria(self):
        ev = RuleBasedEvaluator().evaluate(make_problem(), make_rich_submission())
        assert len(ev.criteria) == 8

    def test_criteria_scores_in_range(self):
        ev = RuleBasedEvaluator().evaluate(make_problem(), make_rich_submission())
        for crit in ev.criteria:
            assert 0 <= crit.score <= 10

    def test_rule_based_is_fallback(self):
        ev = RuleBasedEvaluator().evaluate(make_problem(), make_rich_submission())
        assert ev.is_fallback is True

    def test_many_classes_improve_requirement_score(self):
        evaluator = RuleBasedEvaluator()
        problem = make_problem()
        rich_ev = evaluator.evaluate(problem, make_rich_submission())
        minimal_ev = evaluator.evaluate(problem, make_minimal_submission())
        rich_req = next(c for c in rich_ev.criteria if c.name == "Requirement Understanding")
        min_req = next(c for c in minimal_ev.criteria if c.name == "Requirement Understanding")
        assert rich_req.score > min_req.score

    def test_empty_edge_cases_lowers_edge_case_score(self):
        evaluator = RuleBasedEvaluator()
        problem = make_problem()
        minimal_ev = evaluator.evaluate(problem, make_minimal_submission())
        ec_crit = next(c for c in minimal_ev.criteria if c.name == "Edge Cases & Testability")
        assert ec_crit.score < 7

    def test_interfaces_present_improves_encapsulation_score(self):
        evaluator = RuleBasedEvaluator()
        problem = make_problem()
        sub_with = make_rich_submission()
        sub_without = make_rich_submission()
        sub_without.interfaces = ""
        ev_with = evaluator.evaluate(problem, sub_with)
        ev_without = evaluator.evaluate(problem, sub_without)
        enc_with = next(c for c in ev_with.criteria if c.name == "Encapsulation & Interfaces")
        enc_without = next(c for c in ev_without.criteria if c.name == "Encapsulation & Interfaces")
        assert enc_with.score > enc_without.score

    def test_design_explanation_word_count_affects_score(self):
        evaluator = RuleBasedEvaluator()
        problem = make_problem()
        sub_long = make_rich_submission()  # has 60+ words
        sub_short = make_rich_submission()
        sub_short.design_explanation = "Basic design."
        ev_long = evaluator.evaluate(problem, sub_long)
        ev_short = evaluator.evaluate(problem, sub_short)
        de_long = next(c for c in ev_long.criteria if c.name == "Design Explanation")
        de_short = next(c for c in ev_short.criteria if c.name == "Design Explanation")
        assert de_long.score > de_short.score


class TestAIOutputValidation:

    def test_valid_ai_response_passes_validation(self):
        data = {
            "criteria": [
                {
                    "name": "Class Responsibilities",
                    "score": 7.5,
                    "evidence": "Clear separation of concerns.",
                    "concern": "Minor overlap between Lot and Floor.",
                    "suggestion": "Consider extracting slot assignment.",
                    "confidence": "high",
                }
            ],
            "overall_score": 75.0,
            "summary": "Good design overall.",
            "strengths": ["Clear responsibilities"],
            "improvements": ["Add interfaces"],
        }
        result = AIEvaluationResponse(**data)
        assert result.overall_score == 75.0
        assert len(result.criteria) == 1

    def test_score_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AIEvaluationResponse(
                criteria=[AICriterionResponse(name="X", score=15)],  # > 10
                overall_score=50,
            )

    def test_overall_score_out_of_range_raises_validation_error(self):
        with pytest.raises(ValidationError):
            AIEvaluationResponse(
                criteria=[],
                overall_score=120,  # > 100
            )

    def test_missing_criteria_defaults_to_empty(self):
        result = AIEvaluationResponse(criteria=[], overall_score=50)
        assert result.criteria == []
        assert result.strengths == []

    def test_ai_evaluator_handles_missing_api_key(self, app):
        """AIEvaluator with no key should fall back to RuleBasedEvaluator, not crash."""
        from app.evaluators.ai_evaluator import AIEvaluator
        evaluator = AIEvaluator(api_key="", model="gpt-4o")
        with app.app_context():
            result = evaluator.evaluate(make_problem(), make_rich_submission())
        assert result.status == "completed"
        assert result.is_fallback is True
        assert result.overall_score is not None
