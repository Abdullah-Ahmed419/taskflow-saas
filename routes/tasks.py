"""
routes/tasks.py — Task CRUD API
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from services.task_service import TaskService

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/api/tasks", methods=["GET"])
@login_required
def get_tasks():
    return jsonify([t.to_dict() for t in TaskService.get_all(current_user)])


@tasks_bp.route("/api/tasks", methods=["POST"])
@login_required
def create_task():
    task, err = TaskService.create(current_user, request.get_json())
    if err:
        return jsonify({"error": err}), 403
    return jsonify(task.to_dict()), 201


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task(task_id):
    task = TaskService.get_one(task_id, current_user)
    if not task:
        return jsonify({"error": "Not found"}), 404
    return jsonify(TaskService.update(task, request.get_json()).to_dict())


@tasks_bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task(task_id):
    task = TaskService.get_one(task_id, current_user)
    if not task:
        return jsonify({"error": "Not found"}), 404
    TaskService.delete(task)
    return jsonify({"ok": True})


@tasks_bp.route("/api/tasks/<int:task_id>/notify", methods=["PATCH"])
@login_required
def mark_notified(task_id):
    task = TaskService.get_one(task_id, current_user)
    if task:
        TaskService.mark_notified(task)
    return jsonify({"ok": True})


@tasks_bp.route("/api/tasks/import", methods=["POST"])
@login_required
def import_tasks():
    items = (request.get_json() or {}).get("tasks", [])
    count, err = TaskService.bulk_import(current_user, items)
    if err and count == 0:
        return jsonify({"error": err}), 403
    return jsonify({"imported": count, "warning": err})
