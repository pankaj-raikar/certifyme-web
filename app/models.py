from datetime import datetime
from flask_login import UserMixin
from app.extensions import db, bcrypt


class Admin(db.Model, UserMixin):
    """Admin user account (signup/login)."""

    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    opportunities = db.relationship(
        "Opportunity", backref="admin", cascade="all, delete-orphan"
    )
    password_resets = db.relationship(
        "PasswordReset", backref="admin", cascade="all, delete-orphan"
    )

    def set_password(self, password: str):
        """Hash password with bcrypt (cost=12 = ~100ms per hash — strong security)."""
        self.password_hash = bcrypt.generate_password_hash(password, rounds=12).decode(
            "utf-8"
        )

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)


class Opportunity(db.Model):
    """Internship opportunity posted by an admin."""

    __tablename__ = "opportunities"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    skills = db.Column(db.Text, nullable=False)  # comma-separated
    future_opportunities = db.Column(db.Text, nullable=False)
    max_applicants = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PasswordReset(db.Model):
    """Password reset token — one-time use, 1-hour expiry."""

    __tablename__ = "password_resets"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.id"), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime, nullable=True)
