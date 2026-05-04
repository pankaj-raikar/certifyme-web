import pytest
from app.extensions import db
from app.models import Admin


class TestSignup:
    """US-1.1: Signup tests."""

    def test_signup_success(self, client):
        """Create account with valid data."""
        res = client.post(
            "/api/auth/signup",
            json={
                "full_name": "Charlie Admin",
                "email": "charlie@test.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
        )

        assert res.status_code == 201
        data = res.get_json()
        assert data["full_name"] == "Charlie Admin"
        assert data["email"] == "charlie@test.com"

        # Verify stored in DB
        admin = Admin.query.filter_by(email="charlie@test.com").first()
        assert admin is not None

    def test_signup_duplicate_email(self, client, admin_a):
        """Duplicate email returns 409."""
        res = client.post(
            "/api/auth/signup",
            json={
                "full_name": "Alice Clone",
                "email": "alice@test.com",
                "password": "securepass123",
                "confirm_password": "securepass123",
            },
        )

        assert res.status_code == 409
        assert "already exists" in res.get_json()["error"]

    def test_signup_missing_field(self, client):
        """Missing required field returns 422."""
        res = client.post(
            "/api/auth/signup",
            json={
                "full_name": "Dave Admin",
                "email": "dave@test.com",
                "password": "securepass123",
                # Missing confirm_password
            },
        )

        assert res.status_code == 422
        assert "Validation failed" in res.get_json()["error"]

    def test_signup_short_password(self, client):
        """Password < 8 chars returns 422."""
        res = client.post(
            "/api/auth/signup",
            json={
                "full_name": "Eve Admin",
                "email": "eve@test.com",
                "password": "short",
                "confirm_password": "short",
            },
        )

        assert res.status_code == 422

    def test_signup_mismatched_passwords(self, client):
        """Confirm password != password returns 422."""
        res = client.post(
            "/api/auth/signup",
            json={
                "full_name": "Frank Admin",
                "email": "frank@test.com",
                "password": "securepass123",
                "confirm_password": "securepass456",
            },
        )

        assert res.status_code == 422


class TestLogin:
    """US-1.2: Login tests."""

    def test_login_success(self, client, admin_a):
        """Valid credentials returns 200 with session."""
        res = client.post(
            "/api/auth/login",
            json={
                "email": "alice@test.com",
                "password": "securepass123",
                "remember_me": False,
            },
        )

        assert res.status_code == 200
        data = res.get_json()
        assert data["full_name"] == "Alice Admin"
        assert data["email"] == "alice@test.com"

    def test_login_invalid_email(self, client):
        """Nonexistent email returns 401."""
        res = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "securepass123"},
        )

        assert res.status_code == 401
        assert "Invalid email or password" in res.get_json()["error"]

    def test_login_invalid_password(self, client, admin_a):
        """Wrong password returns 401."""
        res = client.post(
            "/api/auth/login",
            json={"email": "alice@test.com", "password": "wrongpassword"},
        )

        assert res.status_code == 401
        assert "Invalid email or password" in res.get_json()["error"]

    def test_login_generic_error(self, client, admin_a):
        """Error message doesn't leak which field is wrong."""
        # Try wrong email
        res1 = client.post(
            "/api/auth/login",
            json={"email": "fakeemail@test.com", "password": "securepass123"},
        )

        # Try wrong password
        res2 = client.post(
            "/api/auth/login", json={"email": "alice@test.com", "password": "wrongpass"}
        )

        # Same error message
        assert res1.get_json()["error"] == res2.get_json()["error"]


class TestMe:
    """US-1.2: Get current user."""

    def test_me_logged_in(self, client, admin_a):
        """Return current user when logged in."""
        client.post(
            "/api/auth/login",
            json={"email": "alice@test.com", "password": "securepass123"},
        )

        res = client.get("/api/auth/me")

        assert res.status_code == 200
        data = res.get_json()
        assert data["email"] == "alice@test.com"

    def test_me_not_logged_in(self, client):
        """Return 401 when not logged in."""
        res = client.get("/api/auth/me")

        assert res.status_code == 401


class TestLogout:
    """US-1.2: Logout."""

    def test_logout_success(self, client, admin_a):
        """Logout destroys session."""
        # Login first
        client.post(
            "/api/auth/login",
            json={"email": "alice@test.com", "password": "securepass123"},
        )

        # Verify logged in
        assert client.get("/api/auth/me").status_code == 200

        # Logout
        res = client.post("/api/auth/logout")
        assert res.status_code == 200

        # Verify logged out
        assert client.get("/api/auth/me").status_code == 401


class TestForgotPassword:
    """US-1.3: Forgot password."""

    def test_forgot_password_always_200(self, client, admin_a):
        """Always return 200, don't leak existence."""
        # Existing email
        res1 = client.post(
            "/api/auth/forgot-password", json={"email": "alice@test.com"}
        )

        # Nonexistent email
        res2 = client.post(
            "/api/auth/forgot-password", json={"email": "fakeemail@test.com"}
        )

        # Both 200
        assert res1.status_code == 200
        assert res2.status_code == 200
