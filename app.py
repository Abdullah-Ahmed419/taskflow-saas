"""
app.py — TaskFlow SaaS App Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

db       = SQLAlchemy()
login_manager = LoginManager()
bcrypt   = Bcrypt()
csrf     = CSRFProtect()
mail     = Mail()
migrate  = Migrate()


def create_app(config_name: str = None):
    app = Flask(__name__)

    # ── Proxy fix for Railway / Render ─────────────────────────────────────
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # ── Load config ────────────────────────────────────────────────────────
    from config import config_map
    cfg_name = config_name or os.environ.get("FLASK_ENV", "production")
    app.config.from_object(config_map[cfg_name])

    # ── Extensions ─────────────────────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view  = "auth.login_page"
    login_manager.login_message = ""

    # ── Blueprints ─────────────────────────────────────────────────────────
    from routes.auth  import auth_bp
    from routes.tasks import tasks_bp
    from routes.main  import main_bp
    from routes.profile import profile_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(admin_bp)

    # ── Shell context ──────────────────────────────────────────────────────
    @app.shell_context_processor
    def make_shell_context():
        from models.user import User
        from models.task import Task
        from models.subscription import Subscription
        return dict(db=db, User=User, Task=Task, Subscription=Subscription)

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app("development")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
