"""
utils/decorators.py — Route decorators
"""
from functools import wraps
from flask import jsonify, abort
from flask_login import current_user


def admin_required(f):
    """Reject non-admin users with 403."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated


def pro_required(f):
    """Reject free-tier users with 403 JSON."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_pro:
            return jsonify({
                "error": "This feature requires a Pro plan.",
                "upgrade": True,
            }), 403
        return f(*args, **kwargs)
    return decorated
