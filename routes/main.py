"""
routes/main.py — Dashboard + user info
"""
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

from services.task_service import TaskService

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    stats = TaskService.dashboard_stats(current_user)
    return render_template("app.html", user=current_user, stats=stats)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    stats = TaskService.dashboard_stats(current_user)
    return render_template("dashboard.html", user=current_user, stats=stats)


@main_bp.route("/api/me")
@login_required
def me():
    from flask import current_app
    limit = current_app.config.get("FREE_TASK_LIMIT", 10)
    data  = current_user.to_dict()
    data.update({
        "taskCount":     current_user.task_count,
        "freeTaskLimit": limit,
        "canCreate":     current_user.can_create_task(limit),
    })
    return jsonify(data)


@main_bp.route("/api/stats")
@login_required
def stats():
    return jsonify(TaskService.dashboard_stats(current_user))
