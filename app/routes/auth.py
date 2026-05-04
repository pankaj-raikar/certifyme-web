from datetime import datetime, timedelta
from functools import wraps
import secrets
import hashlib
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from email_validator import validate_email, EmailNotValidError
from app.extensions import db
from app.models import Admin, PasswordReset

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """
    US-1.1: Create a new admin account.
    Expected JSON: {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "securepass123",
        "confirm_password": "securepass123"
    }
    """
    try:
        data = request.get_json() or {}

        # Validate required fields
        full_name = data.get("full_name", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        errors = {}

        if not full_name:
            errors["full_name"] = "Full name is required"

        if not email:
            errors["email"] = "Email is required"
        else:
            try:
                # check_deliverability=False allows test domains (test.com, example.com)
                validate_email(email, check_deliverability=False)
            except EmailNotValidError:
                errors["email"] = "Invalid email format"

        if not password:
            errors["password"] = "Password is required"
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"

        if not confirm_password:
            errors["confirm_password"] = "Confirm password is required"
        elif password != confirm_password:
            errors["confirm_password"] = "Passwords do not match"

        if errors:
            return jsonify({"error": "Validation failed", "fields": errors}), 422

        # Check if email already exists
        existing = Admin.query.filter_by(email=email.lower()).first()
        if existing:
            return jsonify({"error": "Account already exists"}), 409

        # Create admin
        admin = Admin(full_name=full_name, email=email.lower())
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        return jsonify(
            {
                "id": admin.id,
                "full_name": admin.full_name,
                "email": admin.email,
                "message": "Account created successfully",
            }
        ), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error during signup")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    US-1.2: Log in an admin with email + password.
    Expected JSON: {
        "email": "john@example.com",
        "password": "securepass123",
        "remember_me": true
    }
    """
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        remember_me = data.get("remember_me", False)

        if not email or not password:
            return jsonify({"error": "Invalid email or password"}), 401

        admin = Admin.query.filter_by(email=email).first()

        # Generic message — don't leak whether email exists
        if not admin or not admin.check_password(password):
            return jsonify({"error": "Invalid email or password"}), 401

        login_user(admin, remember=remember_me)

        return jsonify(
            {
                "id": admin.id,
                "full_name": admin.full_name,
                "email": admin.email,
                "message": "Logged in successfully",
            }
        ), 200

    except Exception as e:
        current_app.logger.exception("Error during login")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """US-1.2: Log out the current admin."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """US-1.2: Return current admin info."""
    return jsonify(
        {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
        }
    ), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    US-1.3: Generate a password reset token.
    Always returns 200 (don't leak whether email exists).
    If email exists, generates token and logs reset URL to console.
    """
    try:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()

        admin = Admin.query.filter_by(email=email).first()

        # Always return 200, but only generate token if admin exists
        if admin:
            token = secrets.token_urlsafe(32)  # 32 bytes = 43 chars in base64
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            expires_at = datetime.utcnow() + timedelta(hours=1)

            reset = PasswordReset(
                admin_id=admin.id, token_hash=token_hash, expires_at=expires_at
            )
            db.session.add(reset)
            db.session.commit()

            # Log the reset URL to console (in production, send email)
            reset_url = f"http://127.0.0.1:5500/admin.html?reset_token={token}"
            print(f"\n*** PASSWORD RESET URL ***\n{reset_url}\n")

        return jsonify(
            {"message": "If an account exists, a password reset email has been sent"}
        ), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error during forgot_password")
        return jsonify({"error": "Internal server error"}), 500


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    US-1.3: Reset password using a token.
    Expected JSON: {
        "token": "token_from_reset_link",
        "password": "newpassword123",
        "confirm_password": "newpassword123"
    }
    """
    try:
        data = request.get_json() or {}
        token = data.get("token", "")
        password = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        # Validate token first before any password checks
        if not token:
            return jsonify({"error": "Invalid or expired token"}), 400

        # Hash the token and look for it
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        reset = PasswordReset.query.filter_by(token_hash=token_hash).first()

        if not reset:
            return jsonify({"error": "Invalid or expired token"}), 400

        # Check expiry
        if datetime.utcnow() > reset.expires_at:
            return jsonify({"error": "Invalid or expired token"}), 400

        # Check if already used
        if reset.used_at is not None:
            return jsonify({"error": "Token already used"}), 400

        # Now validate password
        errors = {}

        if not password:
            errors["password"] = "Password is required"
        elif len(password) < 8:
            errors["password"] = "Password must be at least 8 characters"

        if password != confirm_password:
            errors["confirm_password"] = "Passwords do not match"

        if errors:
            return jsonify({"error": "Validation failed", "fields": errors}), 422

        # Update password
        admin = reset.admin
        admin.set_password(password)
        reset.used_at = datetime.utcnow()
        db.session.commit()

        return jsonify({"message": "Password reset successfully"}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error during reset_password")
        return jsonify({"error": "Internal server error"}), 500
