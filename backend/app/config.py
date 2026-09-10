import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    # Evaluator selection: "ai", "rule_based", "mock"
    EVALUATOR_TYPE = os.environ.get("EVALUATOR_TYPE", "rule_based")

    # OpenAI
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o")
    AI_TIMEOUT = int(os.environ.get("AI_TIMEOUT", "30"))

    # Submission limits
    MAX_SUBMISSION_SIZE = 50_000  # characters


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///lld_platform.db"
    )


class TestingConfig(Config):
    TESTING = True
    EVALUATOR_TYPE = "mock"
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///test_temp.db"




class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///lld_platform.db")


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config() -> Config:
    env = os.environ.get("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)
