"""
config.py — Environment-based configuration
"""
import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session / Cookie security ──────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY  = True
    SESSION_COOKIE_SAMESITE  = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30  # 30 days

    # ── File uploads ───────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024   # 2 MB avatar limit
    UPLOAD_FOLDER      = os.path.join(os.path.dirname(__file__), "static", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

    # ── Mail ───────────────────────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get("MAIL_SERVER",   "smtp.gmail.com")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.environ.get("MAIL_USE_TLS",  "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@taskflow.app")

    # ── Google OAuth ───────────────────────────────────────────────────────
    GOOGLE_CLIENT_ID     = os.environ.get("GOOGLE_CLIENT_ID",     "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")

    # ── App URL (used for OAuth callbacks + emails) ────────────────────────
    APP_URL = os.environ.get("APP_URL", "http://localhost:5000")

    # ── SaaS limits ───────────────────────────────────────────────────────
    FREE_TASK_LIMIT = 10


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///taskflow_dev.db"
    )
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED      = True


class ProductionConfig(BaseConfig):
    DEBUG = False

    _db_url = os.environ.get("DATABASE_URL", "sqlite:///taskflow.db")
    # Railway uses postgres:// — SQLAlchemy needs postgresql://
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url

    SESSION_COOKIE_SECURE  = True   # HTTPS only
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED        = True

    # ── Connection pooling for Postgres ───────────────────────────────────
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }


class TestingConfig(BaseConfig):
    TESTING    = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "testing":     TestingConfig,
    "default":     DevelopmentConfig,
}
