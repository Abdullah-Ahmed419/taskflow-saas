"""
models/task.py — Task model
"""
from datetime import datetime
from app import db


class Task(db.Model):
    __tablename__ = "tasks"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title       = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, default="")
    due_date    = db.Column(db.String(20), default="")
    due_time    = db.Column(db.String(10), default="")
    priority    = db.Column(db.String(20), default="Medium")
    status      = db.Column(db.String(20), default="pending")
    notified    = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "title":     self.title,
            "desc":      self.description,
            "dueDate":   self.due_date,
            "dueTime":   self.due_time,
            "priority":  self.priority,
            "status":    self.status,
            "notified":  self.notified,
            "createdAt": int(self.created_at.timestamp() * 1000),
        }

    def __repr__(self):
        return f"<Task {self.id}: {self.title[:40]}>"
