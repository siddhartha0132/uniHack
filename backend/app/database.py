"""
database.py
-----------
Phase 3: SQLAlchemy engine + session factory.

DATABASE_URL defaults to SQLite (zero-setup for local dev).
Swap in Postgres for production by setting the env var:
    DATABASE_URL=postgresql+psycopg://user:pass@host:5432/veritas

The schema stays the same — all JSON columns, no over-normalization for MVP.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

import re

def normalize_database_url(url: str) -> str:
    if not url:
        return "sqlite:///./veritas.db"
    
    # 1. Scheme normalization for psycopg v3
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        
    # 2. Supabase IPv6 direct host -> IPv4 connection pooler auto-rewrite (for Render)
    match = re.search(r"@db\.([a-z0-9]+)\.supabase\.co(?::\d+)?", url)
    if match:
        project_ref = match.group(1)
        user_pass_match = re.search(r"://([^@]+)@", url)
        if user_pass_match:
            user_pass = user_pass_match.group(1)
            if ":" in user_pass:
                user, password = user_pass.split(":", 1)
                if "." not in user:
                    user = f"{user}.{project_ref}"
                new_user_pass = f"{user}:{password}"
            else:
                user = user_pass
                if "." not in user:
                    user = f"{user}.{project_ref}"
                new_user_pass = user
        region = os.getenv("SUPABASE_REGION", "ap-northeast-2")
        url = re.sub(r"@db\.[a-z0-9]+\.supabase\.co(:\d+)?", f"@aws-0-{region}.pooler.supabase.com:5432", url)
    
    return url

DATABASE_URL = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///./veritas.db"))

# SQLite needs check_same_thread=False for FastAPI's async handlers
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session, ensures it's closed after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables defined in models.py. Called once at startup."""
    from . import models  # noqa: F401 — ensure models are registered
    Base.metadata.create_all(bind=engine)
