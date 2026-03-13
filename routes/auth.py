"""
routes/auth.py — Auth blueprint (email/password + Google OAuth + password reset)
"""
import os, secrets
from urllib.parse import urlencode

import requests as http_requests
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify, current_app)
from flask_login import login_required, logout_user, current_user

from services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__)

GOOGLE_AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USER_URL  = "https://www.googleapis.com/oauth2/v3/userinfo"


# ── Pages ──────────────────────────────────────────────────────────────────

@auth_bp.route("/login")
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth.html", mode="login")


@auth_bp.route("/signup")
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    return render_template("auth.html", mode="signup")


@auth_bp.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot_password.html")


@auth_bp.route("/reset-password/<token>")
def reset_password_page(token):
    return render_template("reset_password.html", token=token)


# ── Email / Password API ───────────────────────────────────────────────────

@auth_bp.route("/api/auth/signup", methods=["POST"])
def signup():
    d = request.get_json()
    user, err = AuthService.signup(
        name     = (d.get("name") or "").strip(),
        email    = (d.get("email") or "").strip(),
        password = d.get("password") or "",
    )
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True, "redirect": url_for("main.index")})


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    d = request.get_json()
    user, err = AuthService.login(
        email    = (d.get("email") or "").strip(),
        password = d.get("password") or "",
    )
    if err:
        return jsonify({"error": err}), 401
    return jsonify({"ok": True, "redirect": url_for("main.index")})


@auth_bp.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    d     = request.get_json()
    email = (d.get("email") or "").strip()
    AuthService.send_reset_email(email)
    # Always return success to prevent email enumeration
    return jsonify({"ok": True, "message": "If that email exists, a reset link has been sent."})


@auth_bp.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    d       = request.get_json()
    token   = d.get("token", "")
    new_pwd = d.get("password", "")
    ok, err = AuthService.reset_password(token, new_pwd)
    if not ok:
        return jsonify({"error": err}), 400
    return jsonify({"ok": True, "redirect": url_for("auth.login_page")})


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login_page"))


# ── Google OAuth ───────────────────────────────────────────────────────────

@auth_bp.route("/auth/google")
def google_login():
    if not current_app.config.get("GOOGLE_CLIENT_ID"):
        flash("Google login is not configured.", "error")
        return redirect(url_for("auth.login_page"))

    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    redirect_uri = url_for("auth.google_callback", _external=True)

    params = {
        "client_id":     current_app.config["GOOGLE_CLIENT_ID"],
        "redirect_uri":  redirect_uri,
        "response_type": "code",
        "scope":         "openid email profile",
        "state":         state,
        "access_type":   "offline",
        "prompt":        "select_account",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@auth_bp.route("/auth/google/callback")
def google_callback():
    if request.args.get("error"):
        flash("Google login was cancelled.", "error")
        return redirect(url_for("auth.login_page"))

    if request.args.get("state") != session.pop("oauth_state", None):
        flash("Invalid OAuth state.", "error")
        return redirect(url_for("auth.login_page"))

    redirect_uri = url_for("auth.google_callback", _external=True)
    token_resp = http_requests.post(GOOGLE_TOKEN_URL, data={
        "code":          request.args.get("code"),
        "client_id":     current_app.config["GOOGLE_CLIENT_ID"],
        "client_secret": current_app.config["GOOGLE_CLIENT_SECRET"],
        "redirect_uri":  redirect_uri,
        "grant_type":    "authorization_code",
    }).json()

    access_token = token_resp.get("access_token")
    if not access_token:
        flash("Failed to get token from Google.", "error")
        return redirect(url_for("auth.login_page"))

    info = http_requests.get(
        GOOGLE_USER_URL,
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    email = info.get("email", "")
    if not email:
        flash("Could not get email from Google.", "error")
        return redirect(url_for("auth.login_page"))

    AuthService.google_find_or_create(
        google_id = info.get("sub"),
        email     = email,
        name      = info.get("name", "User"),
        avatar    = info.get("picture", ""),
    )
    return redirect(url_for("main.index"))
