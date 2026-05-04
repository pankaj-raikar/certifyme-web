import os
from datetime import timedelta


class Config:
    """Base config — shared by all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session config — secure for production
    SESSION_COOKIE_SECURE = False  # True in production (HTTPS only)
    SESSION_COOKIE_HTTPONLY = True  # JS cannot access (prevents XSS theft)
    SESSION_COOKIE_SAMESITE = "Lax"  # Prevents CSRF
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)


class DevelopmentConfig(Config):
    """Local development with file-based SQLite."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///instance/app.db")


class TestingConfig(Config):
    """Fast in-memory SQLite for pytest."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
