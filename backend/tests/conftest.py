"""
Pytest configuration — shared fixtures for the entire test suite.
Uses temporary SQLite database file for isolated, multi-threaded backend tests.
"""
import os
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.models import AttemptModel, EvaluationModel, ProblemModel, SubmissionModel

DB_FILE = "instance/test_temp.db"


@pytest.fixture(scope="session")
def app():
    """Create application with test config (test_temp.db, MockEvaluator)."""
    flask_app = create_app(TestingConfig())
    with flask_app.app_context():
        _db.create_all()
        _seed_problems()
        yield flask_app
        _db.session.remove()
        _db.drop_all()

    # Clean up test DB file after full session run
    db_path = os.path.join(flask_app.root_path, "..", "instance", "test_temp.db")
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture(autouse=True)
def cleanup_data(app):
    """Automatically clean up attempts, submissions, and evaluations after each test."""
    yield
    with app.app_context():
        _db.session.remove()
        EvaluationModel.query.delete()
        SubmissionModel.query.delete()
        AttemptModel.query.delete()
        _db.session.commit()


@pytest.fixture()
def client(app):
    """Return a test client."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Yield db within an app context."""
    with app.app_context():
        yield _db


def _seed_problems():
    """Add minimal test problems."""
    if ProblemModel.query.count() == 0:
        problems = [
            ProblemModel(
                id="prob-parking-001",
                slug="parking-lot",
                title="Parking Lot",
                difficulty="medium",
                short_description="Design a parking lot system.",
                detailed_requirements="Manage vehicle entry, exit, payment and spot assignment.",
                assumptions="Single lot, flat-rate pricing.",
                submission_guidance="Include ParkingLot, Floor, Spot, Ticket, Payment classes.",
            ),
            ProblemModel(
                id="prob-elevator-001",
                slug="elevator-system",
                title="Elevator System",
                difficulty="hard",
                short_description="Design an elevator control system.",
                detailed_requirements="Handle multiple elevators, floor requests, dispatch.",
                assumptions="Constant speed, no weight sensor.",
                submission_guidance="Include Elevator, Dispatcher, FloorRequest classes.",
            ),
        ]
        for p in problems:
            _db.session.add(p)
        _db.session.commit()
