"""
Application settings.

Database URL resolution order (mirrors Engineering-Management-App's pattern,
which exists specifically to avoid a repeat of that app's database-collision
incident): a dedicated SHOPFITTING_DATABASE_URL takes priority so this app
never silently ends up sharing a Postgres instance with another project,
falling back to the generic DATABASE_URL Railway injects, falling back to a
local sqlite file for development.
"""
import os
from pydantic_settings import BaseSettings


def _resolve_database_url() -> str:
    url = os.getenv("SHOPFITTING_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not url:
        return "sqlite:///./shopfitting_dev.db"
    # Railway/Heroku-style URLs use postgres:// ; SQLAlchemy + psycopg v3 need postgresql+psycopg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = _resolve_database_url()
    secret_key: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    algorithm: str = "HS256"


settings = Settings()
