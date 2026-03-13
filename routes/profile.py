"""
routes/profile.py — User profile management
"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user

from services.profile_service import ProfileService

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html", user=current_user)


@profile_bp.route("/api/profile/name", methods=["PUT"])
@login_required
def update_name():
    d = request.get_json()
    ok, err = ProfileService.update_name(current_user, d.get("name", ""))
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True, "name": current_user.name})


@profile_bp.route("/api/profile/avatar", methods=["POST"])
@login_required
def update_avatar():
    file = request.files.get("avatar")
    ok, result = ProfileService.update_avatar(current_user, file)
    if not ok:
        return jsonify({"error": result}), 400
    return jsonify({"ok": True, "avatar": result})


@profile_bp.route("/api/profile/password", methods=["PUT"])
@login_required
def change_password():
    d = request.get_json()
    ok, err = ProfileService.change_password(
        current_user,
        current_pw = d.get("currentPassword", ""),
        new_pw     = d.get("newPassword", ""),
    )
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True})
