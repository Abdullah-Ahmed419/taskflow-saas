"""
routes/admin.py — Admin panel (is_admin=True users only)
"""
from functools import wraps
from flask import Blueprint, render_template, jsonify, redirect, url_for, abort
from flask_login import login_required, current_user

from app import db
from models.user import User
from models.task import Task
from models.subscription import Subscription

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    users = (
        db.session.query(User, Subscription)
        .outerjoin(Subscription, User.id == Subscription.user_id)
        .order_by(User.created_at.desc())
        .all()
    )

    stats = {
        "total_users":     User.query.count(),
        "pro_users":       Subscription.query.filter_by(plan="pro", status="active").count(),
        "total_tasks":     Task.query.count(),
        "completed_tasks": Task.query.filter_by(status="completed").count(),
    }

    return render_template("admin/dashboard.html",
                           users=users, stats=stats)


@admin_bp.route("/api/users")
@login_required
@admin_required
def api_users():
    rows = (
        db.session.query(User, Subscription)
        .outerjoin(Subscription, User.id == Subscription.user_id)
        .order_by(User.created_at.desc())
        .all()
    )
    result = []
    for user, sub in rows:
        d = user.to_dict()
        d["taskCount"]   = user.task_count
        d["plan"]        = sub.plan if sub else "free"
        d["subStatus"]   = sub.status if sub else "none"
        result.append(d)
    return jsonify(result)


@admin_bp.route("/api/users/<int:user_id>/upgrade", methods=["POST"])
@login_required
@admin_required
def upgrade_user(user_id):
    sub = Subscription.get_or_create(user_id)
    sub.plan   = "pro"
    sub.status = "active"
    db.session.commit()
    return jsonify({"ok": True})


@admin_bp.route("/api/users/<int:user_id>/downgrade", methods=["POST"])
@login_required
@admin_required
def downgrade_user(user_id):
    sub = Subscription.get_or_create(user_id)
    sub.plan   = "free"
    sub.status = "active"
    db.session.commit()
    return jsonify({"ok": True})
