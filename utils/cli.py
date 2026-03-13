"""
utils/cli.py — Flask CLI commands for admin operations
Usage:
  flask create-admin email@example.com
  flask send-reminders
  flask set-plan email@example.com pro
"""
import click
from flask import current_app
from flask.cli import with_appcontext


def register_cli(app):
    app.cli.add_command(create_admin)
    app.cli.add_command(send_reminders)
    app.cli.add_command(set_plan)
    app.cli.add_command(list_users)


@click.command("create-admin")
@click.argument("email")
@with_appcontext
def create_admin(email):
    """Promote a user to admin by email."""
    from app import db
    from models.user import User

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        click.echo(f"❌  No user found with email: {email}")
        return
    user.is_admin = True
    db.session.commit()
    click.echo(f"✅  {user.name} ({user.email}) is now an admin.")


@click.command("send-reminders")
@with_appcontext
def send_reminders():
    """Send due-date reminder emails (run daily via cron)."""
    from services.notification_service import NotificationService
    sent = NotificationService.send_due_reminders()
    click.echo(f"✅  Sent {sent} reminder email(s).")


@click.command("set-plan")
@click.argument("email")
@click.argument("plan", type=click.Choice(["free", "pro"]))
@with_appcontext
def set_plan(email, plan):
    """Manually set a user's subscription plan."""
    from app import db
    from models.user import User
    from models.subscription import Subscription

    user = User.query.filter_by(email=email.lower()).first()
    if not user:
        click.echo(f"❌  No user found with email: {email}")
        return

    sub = Subscription.get_or_create(user.id)
    sub.plan   = plan
    sub.status = "active"
    db.session.commit()
    click.echo(f"✅  {user.email} is now on the {plan} plan.")


@click.command("list-users")
@with_appcontext
def list_users():
    """Print a table of all users and their plans."""
    from models.user import User

    users = User.query.order_by(User.created_at.desc()).all()
    click.echo(f"\n{'ID':<6} {'Email':<35} {'Plan':<8} {'Tasks':<8} {'Admin'}")
    click.echo("─" * 65)
    for u in users:
        click.echo(
            f"{u.id:<6} {u.email:<35} {u.plan:<8} {u.task_count:<8} {'✓' if u.is_admin else ''}"
        )
    click.echo(f"\nTotal: {len(users)} user(s)\n")
