"""Tests for problem retrieval."""
import pytest


class TestProblems:

    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"

    def test_list_problems_returns_seeded_problems(self, client):
        resp = client.get("/api/problems")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        problems = data["data"]
        assert len(problems) >= 1

    def test_list_problems_has_required_fields(self, client):
        resp = client.get("/api/problems")
        problems = resp.get_json()["data"]
        for p in problems:
            assert "id" in p
            assert "slug" in p
            assert "title" in p
            assert "difficulty" in p
            assert "short_description" in p

    def test_get_problem_by_id(self, client):
        resp = client.get("/api/problems/prob-parking-001")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["title"] == "Parking Lot"
        assert data["slug"] == "parking-lot"

    def test_get_problem_by_slug(self, client):
        resp = client.get("/api/problems/parking-lot")
        assert resp.status_code == 200
        data = resp.get_json()["data"]
        assert data["title"] == "Parking Lot"

    def test_get_nonexistent_problem_returns_404(self, client):
        resp = client.get("/api/problems/does-not-exist")
        assert resp.status_code == 404
        data = resp.get_json()
        assert data["status"] == "error"
