"""
services/notification_service.py — Email notifications & due-date reminders
"""
from __future__ import annotations
from datetime import date, timedelta

from flask import current_app, render_template_string
from flask_mail import Message

from app import db, mail
from models.task import Task
from models.user import User


# ── Email templates ─────────────────────────────────────────────────────────

_RESET_TMPL = """
<html><body style="font-family:sans-serif;max-width:520px;margin:auto;color:#1a1a1a">
<div style="background:#C8F135;padding:20px 30px;border-radius:12px 12px 0 0">
  <h2 style="margin:0;color:#0D0D0F">🔐 Reset your password</h2>
</div>
<div style="background:#f9f9f9;padding:30px;border-radius:0 0 12px 12px">
  <p>Hi {{ name }},</p>
  <p>Click the button below to reset your TaskFlow password. This link expires in <strong>1 hour</strong>.</p>
  <a href="{{ url }}" style="display:inline-block;margin:20px 0;padding:14px 28px;
     background:#C8F135;color:#0D0D0F;text-decoration:none;border-radius:8px;font-weight:700">
    Reset Password
  </a>
  <p style="color:#666;font-size:13px">If you didn't request this, ignore this email.</p>
</div>
</body></html>
"""

_REMINDER_TMPL = """
<html><body style="font-family:sans-serif;max-width:520px;margin:auto;color:#1a1a1a">
<div style="background:#C8F135;padding:20px 30px;border-radius:12px 12px 0 0">
  <h2 style="margin:0;color:#0D0D0F">⏰ Task reminder</h2>
</div>
<div style="background:#f9f9f9;padding:30px;border-radius:0 0 12px 12px">
  <p>Hi {{ name }},</p>
  <p>You have {{ count }} task(s) due {{ when }}:</p>
  <ul>
    {% for t in tasks %}
    <li style="margin-bottom:8px">
      <strong>{{ t.title }}</strong>
      {% if t.due_time %} at {{ t.due_time }}{% endif %}
      <span style="background:#e0e0e0;border-radius:4px;padding:2px 8px;font-size:12px;margin-left:8px">
        {{ t.priority }}
      </span>
    </li>
    {% endfor %}
  </ul>
  <a href="{{ app_url }}" style="display:inline-block;margin-top:16px;padding:12px 24px;
     background:#C8F135;color:#0D0D0F;text-decoration:none;border-radius:8px;font-weight:700">
    Open TaskFlow
  </a>
</div>
</body></html>
"""


class NotificationService:

    @staticmethod
    def send_password_reset_email(user: User, reset_url: str) -> None:
        html = render_template_string(_RESET_TMPL, name=user.name, url=reset_url)
        msg  = Message(
            subject   = "Reset your TaskFlow password",
            recipients = [user.email],
            html       = html,
        )
        try:
            mail.send(msg)
        except Exception as exc:
            current_app.logger.error("Failed to send reset email: %s", exc)

    @staticmethod
    def send_due_reminders() -> int:
        """
        Send reminder emails for tasks due today or tomorrow.
        Call this from a cron job / scheduler once per day.
        Returns the number of emails sent.
        """
        today    = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        # Find un-notified tasks due today or tomorrow
        tasks = (
            Task.query
            .filter(Task.status != "completed")
            .filter(Task.notified == False)
            .filter(Task.due_date.in_([today, tomorrow]))
            .all()
        )

        # Group by user
        by_user: dict[int, list[Task]] = {}
        for t in tasks:
            by_user.setdefault(t.user_id, []).append(t)

        sent = 0
        for user_id, user_tasks in by_user.items():
            user = User.query.get(user_id)
            if not user:
                continue

            today_tasks    = [t for t in user_tasks if t.due_date == today]
            tomorrow_tasks = [t for t in user_tasks if t.due_date == tomorrow]

            for group, when in [(today_tasks, "today"), (tomorrow_tasks, "tomorrow")]:
                if not group:
                    continue
                html = render_template_string(
                    _REMINDER_TMPL,
                    name=user.name,
                    count=len(group),
                    tasks=group,
                    when=when,
                    app_url=current_app.config.get("APP_URL", "http://localhost:5000"),
                )
                msg = Message(
                    subject    = f"⏰ You have {len(group)} task(s) due {when}",
                    recipients = [user.email],
                    html       = html,
                )
                try:
                    mail.send(msg)
                    # Mark notified
                    for t in group:
                        t.notified = True
                    db.session.commit()
                    sent += 1
                except Exception as exc:
                    current_app.logger.error(
                        "Reminder email failed for user %s: %s", user.email, exc
                    )

        return sent
