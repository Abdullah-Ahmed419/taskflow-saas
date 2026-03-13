"""
services/auth_service.py — Authentication & password-reset logic
"""
from __future__ import annotations
import secrets
from datetime import datetime, timedelta

from flask import current_app, url_for
from flask_login import login_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app import db, bcrypt
from models.user import User
from models.subscription import Subscription
from services.notification_service import NotificationService


class AuthService:

    # ── Email / Password ───────────────────────────────────────────────────

    @staticmethod
    def signup(name: str, email: str, password: str) -> tuple[User | None, str | None]:
        """Create new account. Returns (user, error)."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            return None, "An account with that email already exists."
        if len(password) < 6:
            return None, "Password must be at least 6 characters."

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(name=name.strip(), email=email, password=hashed)
        db.session.add(user)
        db.session.flush()                          # get user.id

        # Create free subscription
        sub = Subscription(user_id=user.id, plan="free")
        db.session.add(sub)
        db.session.commit()

        login_user(user, remember=True)
        return user, None

    @staticmethod
    def login(email: str, password: str) -> tuple[User | None, str | None]:
        """Validate credentials. Returns (user, error)."""
        email = email.strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user or not user.password:
            return None, "Invalid email or password."
        if not bcrypt.check_password_hash(user.password, password):
            return None, "Invalid email or password."
        login_user(user, remember=True)
        return user, None

    # ── Google OAuth ───────────────────────────────────────────────────────

    @staticmethod
    def google_find_or_create(google_id: str, email: str,
                               name: str, avatar: str) -> User:
        """Find or create user from Google profile."""
        user = User.query.filter_by(google_id=google_id).first()
        if not user:
            user = User.query.filter_by(email=email.lower()).first()
            if user:
                user.google_id = google_id
                user.avatar    = avatar
            else:
                user = User(email=email.lower(), name=name,
                            avatar=avatar, google_id=google_id)
                db.session.add(user)
                db.session.flush()
                db.session.add(Subscription(user_id=user.id, plan="free"))

        db.session.commit()
        login_user(user, remember=True)
        return user

    # ── Password Reset ─────────────────────────────────────────────────────

    @staticmethod
    def _serializer() -> URLSafeTimedSerializer:
        return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

    @classmethod
    def send_reset_email(cls, email: str) -> bool:
        """Generate reset token and send email. Returns True if user found."""
        user = User.query.filter_by(email=email.strip().lower()).first()
        if not user:
            return False

        token = cls._serializer().dumps(user.email, salt="pw-reset")
        user.reset_token = token
        db.session.commit()

        reset_url = url_for("auth.reset_password_page",
                            token=token, _external=True)
        NotificationService.send_password_reset_email(user, reset_url)
        return True

    @classmethod
    def reset_password(cls, token: str, new_password: str) -> tuple[bool, str]:
        """Validate token and update password. Returns (ok, error)."""
        try:
            email = cls._serializer().loads(token, salt="pw-reset", max_age=3600)
        except SignatureExpired:
            return False, "Reset link has expired. Please request a new one."
        except BadSignature:
            return False, "Invalid reset link."

        user = User.query.filter_by(email=email).first()
        if not user or user.reset_token != token:
            return False, "Reset link is no longer valid."
        if len(new_password) < 6:
            return False, "Password must be at least 6 characters."

        user.password    = bcrypt.generate_password_hash(new_password).decode("utf-8")
        user.reset_token = None
        db.session.commit()
        return True, ""
