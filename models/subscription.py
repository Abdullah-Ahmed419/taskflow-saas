"""
models/subscription.py — Subscription / billing model
"""
from datetime import datetime
from app import db


class Subscription(db.Model):
    __tablename__ = "subscriptions"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"),
                           unique=True, nullable=False, index=True)

    # "free" | "pro"
    plan       = db.Column(db.String(20), nullable=False, default="free")

    # For Stripe integration later
    stripe_customer_id    = db.Column(db.String(255), nullable=True)
    stripe_subscription_id = db.Column(db.String(255), nullable=True)

    status        = db.Column(db.String(30), default="active")   # active | cancelled | past_due
    started_at    = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at    = db.Column(db.DateTime, nullable=True)         # None = never expires
    cancelled_at  = db.Column(db.DateTime, nullable=True)

    @property
    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "plan":      self.plan,
            "status":    self.status,
            "isActive":  self.is_active,
            "expiresAt": self.expires_at.isoformat() if self.expires_at else None,
        }

    @staticmethod
    def get_or_create(user_id: int) -> "Subscription":
        sub = Subscription.query.filter_by(user_id=user_id).first()
        if not sub:
            sub = Subscription(user_id=user_id, plan="free")
            db.session.add(sub)
            db.session.commit()
        return sub

    def __repr__(self):
        return f"<Subscription user={self.user_id} plan={self.plan}>"
