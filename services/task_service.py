"""
services/task_service.py — Task business logic & plan enforcement
"""
from __future__ import annotations
from flask import current_app
from app import db
from models.task import Task
from models.user import User


class TaskService:

    @staticmethod
    def get_all(user: User) -> list[Task]:
        return Task.query.filter_by(user_id=user.id)\
                         .order_by(Task.created_at.desc()).all()

    @staticmethod
    def get_one(task_id: int, user: User) -> Task | None:
        return Task.query.filter_by(id=task_id, user_id=user.id).first()

    @staticmethod
    def create(user: User, data: dict) -> tuple[Task | None, str | None]:
        """Create task, enforcing plan limits. Returns (task, error)."""
        limit = current_app.config.get("FREE_TASK_LIMIT", 10)
        if not user.can_create_task(limit):
            return None, (
                f"Free plan is limited to {limit} tasks. "
                "Upgrade to Pro for unlimited tasks."
            )

        task = Task(
            user_id     = user.id,
            title       = data.get("title", "Untitled")[:500],
            description = data.get("desc", ""),
            due_date    = data.get("dueDate", ""),
            due_time    = data.get("dueTime", ""),
            priority    = data.get("priority", "Medium"),
            status      = data.get("status", "pending"),
        )
        db.session.add(task)
        db.session.commit()
        return task, None

    @staticmethod
    def update(task: Task, data: dict) -> Task:
        task.title       = data.get("title",    task.title)
        task.description = data.get("desc",     task.description)
        task.due_date    = data.get("dueDate",  task.due_date)
        task.due_time    = data.get("dueTime",  task.due_time)
        task.priority    = data.get("priority", task.priority)
        task.status      = data.get("status",   task.status)
        task.notified    = data.get("notified", task.notified)
        db.session.commit()
        return task

    @staticmethod
    def delete(task: Task) -> None:
        db.session.delete(task)
        db.session.commit()

    @staticmethod
    def mark_notified(task: Task) -> None:
        task.notified = True
        db.session.commit()

    @staticmethod
    def bulk_import(user: User, items: list[dict]) -> tuple[int, str | None]:
        limit = current_app.config.get("FREE_TASK_LIMIT", 10)
        current = user.task_count
        if not user.is_pro and (current + len(items)) > limit:
            allowed = max(0, limit - current)
            if allowed == 0:
                return 0, f"Task limit reached ({limit} tasks on free plan)."
            items = items[:allowed]

        for d in items:
            db.session.add(Task(
                user_id     = user.id,
                title       = d.get("title", "Untitled")[:500],
                description = d.get("desc", ""),
                due_date    = d.get("dueDate", ""),
                due_time    = d.get("dueTime", ""),
                priority    = d.get("priority", "Medium"),
                status      = d.get("status", "pending"),
            ))
        db.session.commit()
        return len(items), None

    @staticmethod
    def dashboard_stats(user: User) -> dict:
        tasks = Task.query.filter_by(user_id=user.id).all()
        total     = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        pending   = total - completed
        overdue   = sum(
            1 for t in tasks
            if t.status != "completed" and t.due_date
        )
        pct = round(completed / total * 100) if total else 0
        return {
            "total":     total,
            "completed": completed,
            "pending":   pending,
            "overdue":   overdue,
            "pct":       pct,
        }
