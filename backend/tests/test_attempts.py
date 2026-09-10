"""Tests for attempt creation, submission, evaluation, and history."""
import json
import time
import pytest


VALID_SUBMISSION = {
    "assumptions": "Single lot, flat rate pricing per hour.",
    "classes": [
        {
            "name": "ParkingLot",
            "responsibility": "Manages floors and overall parking state",
            "methods": ["enterVehicle", "exitVehicle", "getOccupancy"],
            "notes": "Singleton per lot",
        },
        {
            "name": "ParkingFloor",
            "responsibility": "Manages spots on a single floor",
            "methods": ["getAvailableSpot", "markOccupied", "markFree"],
            "notes": "",
        },
        {
            "name": "ParkingSpot",
            "responsibility": "Represents a single parking spot with its state",
            "methods": ["isAvailable", "occupy", "free"],
            "notes": "Has spot type: Small, Medium, Large",
        },
        {
            "name": "Ticket",
            "responsibility": "Holds entry time and vehicle info for fee calculation",
            "methods": ["getEntryTime", "getVehicle"],
            "notes": "",
        },
        {
            "name": "PaymentProcessor",
            "responsibility": "Interface for processing payments",
            "methods": ["processPayment"],
            "notes": "Implemented by CashProcessor, CardProcessor",
        },
    ],
    "interfaces": "PaymentProcessor: processPayment(amount) -> Receipt\nSpotAssignmentStrategy: findSpot(vehicle, floors) -> Spot",
    "relationships": "ParkingLot has-many ParkingFloor. ParkingFloor has-many ParkingSpot. Ticket references Vehicle and ParkingSpot.",
    "design_explanation": (
        "I chose to separate spot assignment into a Strategy interface to allow different algorithms "
        "(nearest first, random, etc.) without changing ParkingLot. Payment is also behind an interface "
        "so new payment methods can be added without modifying the core flow. "
        "Trade-off: using a Strategy pattern adds a small abstraction cost but significantly improves extensibility."
    ),
    "edge_cases": "Lot full: return error, no ticket issued. Concurrent entry: use floor-level locks. Invalid ticket on exit: reject.",
}


class TestAttemptCreation:

    def test_create_attempt_success(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "ok"
        attempt = data["data"]
        assert attempt["problem_id"] == "prob-parking-001"
        assert attempt["status"] == "in_progress"
        assert attempt["attempt_number"] == 1

    def test_create_attempt_invalid_problem_returns_404(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "nonexistent-999"})
        assert resp.status_code == 404

    def test_create_attempt_missing_problem_id_returns_422(self, client):
        resp = client.post("/api/attempts", json={})
        assert resp.status_code == 422

    def test_attempt_number_increments(self, client):
        client.post("/api/attempts", json={"problem_id": "prob-elevator-001", "learner_id": "tester-seq"})
        resp2 = client.post("/api/attempts", json={"problem_id": "prob-elevator-001", "learner_id": "tester-seq"})
        attempt = resp2.get_json()["data"]
        assert attempt["attempt_number"] == 2

    def test_get_attempt_by_id(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        attempt_id = resp.get_json()["data"]["id"]
        get_resp = client.get(f"/api/attempts/{attempt_id}")
        assert get_resp.status_code == 200
        assert get_resp.get_json()["data"]["id"] == attempt_id

    def test_get_nonexistent_attempt_returns_404(self, client):
        resp = client.get("/api/attempts/nonexistent-id")
        assert resp.status_code == 404


class TestSubmission:

    def _create_attempt(self, client, problem_id="prob-parking-001"):
        resp = client.post("/api/attempts", json={"problem_id": problem_id})
        return resp.get_json()["data"]["id"]

    def test_empty_submission_rejected(self, client):
        attempt_id = self._create_attempt(client)
        resp = client.post(
            f"/api/attempts/{attempt_id}/submissions",
            json={"classes": [], "design_explanation": ""},
        )
        assert resp.status_code == 422

    def test_valid_submission_accepted(self, client):
        attempt_id = self._create_attempt(client)
        resp = client.post(
            f"/api/attempts/{attempt_id}/submissions",
            json=VALID_SUBMISSION,
        )
        assert resp.status_code == 202

    def test_submission_triggers_evaluation(self, client):
        attempt_id = self._create_attempt(client)
        client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        # Wait briefly for background thread
        time.sleep(2)
        resp = client.get(f"/api/attempts/{attempt_id}/evaluation")
        assert resp.status_code == 200
        eval_data = resp.get_json()["data"]
        assert eval_data["status"] in ("evaluating", "completed")

    def test_duplicate_submission_rejected(self, client):
        attempt_id = self._create_attempt(client)
        client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        resp2 = client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        assert resp2.status_code == 409

    def test_submission_persisted_before_evaluation(self, client):
        """Submission should be in DB even before evaluation completes."""
        attempt_id = self._create_attempt(client)
        resp = client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        assert resp.status_code == 202
        # Immediately check — submission should exist
        attempt_resp = client.get(f"/api/attempts/{attempt_id}")
        attempt_data = attempt_resp.get_json()["data"]
        assert attempt_data["submission"] is not None

    def test_submission_on_nonexistent_attempt_returns_404(self, client):
        resp = client.post("/api/attempts/nonexistent/submissions", json=VALID_SUBMISSION)
        assert resp.status_code == 404

    def test_submission_class_count_present(self, client):
        attempt_id = self._create_attempt(client)
        client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        attempt_resp = client.get(f"/api/attempts/{attempt_id}")
        submission = attempt_resp.get_json()["data"]["submission"]
        assert len(submission["classes"]) == 5


class TestEvaluation:

    def _create_and_submit(self, client, problem_id="prob-parking-001"):
        attempt_resp = client.post("/api/attempts", json={"problem_id": problem_id})
        attempt_id = attempt_resp.get_json()["data"]["id"]
        client.post(f"/api/attempts/{attempt_id}/submissions", json=VALID_SUBMISSION)
        time.sleep(2)  # wait for background eval
        return attempt_id

    def test_evaluation_completes(self, client):
        attempt_id = self._create_and_submit(client)
        resp = client.get(f"/api/attempts/{attempt_id}/evaluation")
        assert resp.status_code == 200
        ev = resp.get_json()["data"]
        assert ev["status"] == "completed"

    def test_evaluation_has_criteria(self, client):
        attempt_id = self._create_and_submit(client)
        ev = client.get(f"/api/attempts/{attempt_id}/evaluation").get_json()["data"]
        assert len(ev["criteria"]) == 8

    def test_evaluation_criteria_have_all_fields(self, client):
        attempt_id = self._create_and_submit(client)
        ev = client.get(f"/api/attempts/{attempt_id}/evaluation").get_json()["data"]
        for crit in ev["criteria"]:
            assert "name" in crit
            assert "score" in crit
            assert "evidence" in crit
            assert "concern" in crit
            assert "suggestion" in crit
            assert "confidence" in crit

    def test_evaluation_overall_score_present(self, client):
        attempt_id = self._create_and_submit(client)
        ev = client.get(f"/api/attempts/{attempt_id}/evaluation").get_json()["data"]
        assert ev["overall_score"] is not None
        assert 0 <= ev["overall_score"] <= 100

    def test_evaluation_strengths_and_improvements(self, client):
        attempt_id = self._create_and_submit(client)
        ev = client.get(f"/api/attempts/{attempt_id}/evaluation").get_json()["data"]
        assert isinstance(ev["strengths"], list)
        assert isinstance(ev["improvements"], list)

    def test_evaluation_is_fallback_marked(self, client):
        attempt_id = self._create_and_submit(client)
        ev = client.get(f"/api/attempts/{attempt_id}/evaluation").get_json()["data"]
        # Mock evaluator is used in tests — should be marked as fallback
        assert ev["is_fallback"] is True

    def test_no_evaluation_before_submission(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        attempt_id = resp.get_json()["data"]["id"]
        ev_resp = client.get(f"/api/attempts/{attempt_id}/evaluation")
        assert ev_resp.status_code == 404


class TestRetryEvaluation:

    def test_retry_fails_on_non_failed_attempt(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        attempt_id = resp.get_json()["data"]["id"]
        retry_resp = client.post(f"/api/attempts/{attempt_id}/evaluation/retry")
        assert retry_resp.status_code == 422


class TestAttemptHistory:

    def test_list_attempts_returns_all(self, client):
        learner = "history-test-learner"
        client.post("/api/attempts", json={"problem_id": "prob-parking-001", "learner_id": learner})
        client.post("/api/attempts", json={"problem_id": "prob-elevator-001", "learner_id": learner})
        resp = client.get(f"/api/attempts?learner_id={learner}")
        assert resp.status_code == 200
        attempts = resp.get_json()["data"]
        assert len(attempts) >= 2

    def test_attempts_include_problem_info(self, client):
        learner = "history-test-learner-2"
        client.post("/api/attempts", json={"problem_id": "prob-parking-001", "learner_id": learner})
        resp = client.get(f"/api/attempts?learner_id={learner}")
        attempts = resp.get_json()["data"]
        assert attempts[0]["problem"] is not None
        assert attempts[0]["problem"]["title"] is not None


class TestAttemptDeletion:

    def test_delete_attempt_success(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        attempt_id = resp.get_json()["data"]["id"]

        del_resp = client.delete(f"/api/attempts/{attempt_id}")
        assert del_resp.status_code == 204

        # Attempt should now be 404
        get_resp = client.get(f"/api/attempts/{attempt_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_attempt_returns_404(self, client):
        resp = client.delete("/api/attempts/nonexistent-id-999")
        assert resp.status_code == 404

    def test_delete_attempt_with_submission_and_evaluation(self, client):
        resp = client.post("/api/attempts", json={"problem_id": "prob-parking-001"})
        attempt_id = resp.get_json()["data"]["id"]

        # Submit to create submission + evaluation + criteria
        client.post(
            f"/api/attempts/{attempt_id}/submissions",
            json={
                "code": "class ParkingLot:\n    pass\nclass Level:\n    pass\n",
                "design_explanation": "Modular design with parking spots and levels.",
                "tradeoffs": "Tradeoff between memory and search time.",
                "edge_cases": "Full lot handled by checking availability.",
            },
        )

        # Delete the attempt
        del_resp = client.delete(f"/api/attempts/{attempt_id}")
        assert del_resp.status_code == 204

        # Verify attempt and its evaluation cannot be retrieved
        assert client.get(f"/api/attempts/{attempt_id}").status_code == 404
        assert client.get(f"/api/attempts/{attempt_id}/evaluation").status_code == 404

