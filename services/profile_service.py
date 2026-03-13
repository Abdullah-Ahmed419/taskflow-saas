"""
services/profile_service.py — User profile updates
"""
from __future__ import annotations
import os
import uuid
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from flask import current_app
from app import db, bcrypt
from models.user import User


def _allowed(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif", "webp"})


class ProfileService:

    @staticmethod
    def update_name(user: User, name: str) -> tuple[bool, str]:
        name = name.strip()
        if not name:
            return False, "Name cannot be empty."
        user.name = name
        db.session.commit()
        return True, ""

    @staticmethod
    def update_avatar(user: User, file: FileStorage) -> tuple[bool, str]:
        if not file or not file.filename:
            return False, "No file provided."
        if not _allowed(file.filename):
            return False, "Only image files are allowed (png, jpg, jpeg, gif, webp)."

        upload_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_dir, exist_ok=True)

        ext      = file.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        path     = os.path.join(upload_dir, filename)
        file.save(path)

        # Delete old local avatar if it exists
        if user.avatar and user.avatar.startswith("/static/uploads/"):
            old_path = os.path.join(
                current_app.root_path, user.avatar.lstrip("/")
            )
            if os.path.exists(old_path):
                os.remove(old_path)

        user.avatar = f"/static/uploads/{filename}"
        db.session.commit()
        return True, user.avatar

    @staticmethod
    def change_password(user: User, current_pw: str,
                        new_pw: str) -> tuple[bool, str]:
        if not user.password:
            return False, "OAuth accounts cannot set a password this way."
        if not bcrypt.check_password_hash(user.password, current_pw):
            return False, "Current password is incorrect."
        if len(new_pw) < 6:
            return False, "New password must be at least 6 characters."
        user.password = bcrypt.generate_password_hash(new_pw).decode("utf-8")
        db.session.commit()
        return True, ""
