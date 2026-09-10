"""
Flask application factory.
"""
from __future__ import annotations

import logging

from flask import Flask
from flask_cors import CORS

from app.config import get_config
from app.extensions import db
from app.api.routes import api_bp
from app.services import create_practice_service


def create_app(config=None) -> Flask:
    app = Flask(__name__)

    # Load config
    cfg = config or get_config()
    app.config.from_object(cfg)

    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    # CORS
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("FRONTEND_URL", "*")}},
        supports_credentials=True,
    )

    # DB
    db.init_app(app)
    with app.app_context():
        db.create_all()

    # Blueprint
    app.register_blueprint(api_bp)

    # Attach service to app (singleton per app instance)
    app.practice_service = create_practice_service(cfg)

    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    return app
