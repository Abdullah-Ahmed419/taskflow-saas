"""
models/user.py — User model
"""
from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name       = db.Column(db.String(255), nullable=False)
    avatar     = db.Column(db.String(512), nullable=True)
    password   = db.Column(db.String(255), nullable=True)   # None for OAuth users
    google_id  = db.Column(db.String(255), unique=True, nullable=True)
    is_admin   = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Password-reset token (signed, expiry handled by itsdangerous)
    reset_token = db.Column(db.String(512), nullable=True)

    # Relationships
    tasks        = db.relationship("Task", backref="owner", lazy="dynamic",
                                   cascade="all, delete-orphan")
    subscription = db.relationship("Subscription", backref="user",
                                   uselist=False, cascade="all, delete-orphan")

    # ── Helpers ────────────────────────────────────────────────────────────

    def has_password(self) -> bool:
        return self.password is not None

    @property
    def plan(self) -> str:
        if self.subscription and self.subscription.is_active:
            return self.subscription.plan
        return "free"

    @property
    def is_pro(self) -> bool:
        return self.plan == "pro"

    @property
    def task_count(self) -> int:
        return self.tasks.count()

    def can_create_task(self, free_limit: int = 10) -> bool:
        if self.is_pro:
            return True
        return self.task_count < free_limit

    def avatar_url(self) -> str:
        if self.avatar:
            return self.avatar
        return f"https://ui-avatars.com/api/?name={self.name}&background=C8F135&color=0D0D0F&bold=true"

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "email":     self.email,
            "name":      self.name,
            "avatar":    self.avatar_url(),
            "plan":      self.plan,
            "is_admin":  self.is_admin,
            "createdAt": int(self.created_at.timestamp() * 1000),
        }

    def __repr__(self):
        return f"<User {self.email} [{self.plan}]>"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
