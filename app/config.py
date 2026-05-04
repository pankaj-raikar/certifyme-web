import os
from datetime import timedelta


def _get_session_lifetime():
    """Get session lifetime from environment with fallback."""
    try:
        days = int(os.getenv("SESSION_LIFETIME_DAYS", "7"))
    except (ValueError, TypeError):
        days = 7
    return timedelta(days=days)


class Config:
    """Base config — shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY")  # No default - must be set explicitly
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session config — secure by default
    SESSION_COOKIE_SECURE = True  # HTTPS only by default
    SESSION_COOKIE_HTTPONLY = True  # JS cannot access (prevents XSS theft)
    SESSION_COOKIE_SAMESITE = "Lax"  # Prevents CSRF
    PERMANENT_SESSION_LIFETIME = _get_session_lifetime()


class DevelopmentConfig(Config):
    """Local development with file-based SQLite."""

    DEBUG = True
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "dev-key-insecure"
    )  # Allow insecure default for dev
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class TestingConfig(Config):
    """Fast in-memory SQLite for pytest."""

    TESTING = True
    SECRET_KEY = "test-secret-key"  # Fixed key for testing
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False  # Allow HTTP in testing


class ProductionConfig(Config):
    """Production configuration with strict security requirements."""

    DEBUG = False
    TESTING = False

    def __init__(self):
        # Validate required environment variables
        if not os.getenv("SECRET_KEY"):
            raise ValueError(
                "SECRET_KEY environment variable is required for production"
            )
        if not os.getenv("SQLALCHEMY_DATABASE_URI"):
            raise ValueError(
                "SQLALCHEMY_DATABASE_URI environment variable is required for production"
            )
        # SESSION_COOKIE_SECURE is already True in base Config
