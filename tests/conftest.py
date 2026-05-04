import sys
from pathlib import Path

# Add project root to Python path so pytest can find the app module
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models import Admin


@pytest.fixture
def app():
    """Create test app with in-memory SQLite."""
    app = create_app(TestingConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def admin_a(app):
    """Pre-created admin A for testing ownership.

    Returns a dict with admin data to avoid SQLAlchemy detached instance errors.
    """
    with app.app_context():
        admin = Admin(full_name="Alice Admin", email="alice@test.com")
        admin.set_password("securepass123")
        db.session.add(admin)
        db.session.commit()
        return {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "password": "securepass123",
        }


@pytest.fixture
def admin_b(app):
    """Pre-created admin B for testing isolation.

    Returns a dict with admin data to avoid SQLAlchemy detached instance errors.
    """
    with app.app_context():
        admin = Admin(full_name="Bob Admin", email="bob@test.com")
        admin.set_password("securepass123")
        db.session.add(admin)
        db.session.commit()
        return {
            "id": admin.id,
            "email": admin.email,
            "full_name": admin.full_name,
            "password": "securepass123",
        }


@pytest.fixture
def login_admin_a(client, admin_a):
    """Helper to log in admin A and return client."""
    client.post(
        "/api/auth/login",
        json={"email": admin_a["email"], "password": admin_a["password"]},
    )
    return client
