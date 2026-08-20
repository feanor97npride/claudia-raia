import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _resolve_database_uri():
    """Postgres in production via DATABASE_URL; local SQLite file otherwise.

    Some managed Postgres providers hand out `postgres://` URLs, which
    SQLAlchemy's psycopg2 dialect no longer accepts — normalize to
    `postgresql://`.
    """
    # Different managed-Postgres integrations inject different env var names
    # (plain DATABASE_URL, or Vercel's native Postgres/Neon integration which
    # uses the POSTGRES_* family) — accept whichever is present.
    url = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("POSTGRES_URL_NON_POOLING")
    )
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    is_serverless = bool(os.environ.get("VERCEL"))
    db_dir = "/tmp" if is_serverless else BASE_DIR
    return f"sqlite:///{os.path.join(db_dir, 'governanca_ti.db')}"


class Config:
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-governanca-ti-secret")
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True} if not SQLALCHEMY_DATABASE_URI.startswith("sqlite") else {}
    )
