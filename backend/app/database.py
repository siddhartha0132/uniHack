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
        
    # 2. Extract project_ref from URL itself (most reliable) before falling back to env var.
    project_ref = None
    db_match = re.search(r"@db\.([a-z0-9]+)\.supabase\.co", url)
    if db_match:
        project_ref = db_match.group(1)
    
    # 2a. Supabase direct host -> IPv4 connection pooler rewrite (if not already pooler)
    if "db." in url and "supabase.co" in url and "pooler" not in url:
        if not project_ref:
            project_ref = db_match.group(1) if db_match else None
        if project_ref:
            region = os.getenv("SUPABASE_REGION", "ap-northeast-2")
            url = re.sub(r"@db\.[a-z0-9]+\.supabase\.co(:\d+)?", f"@aws-0-{region}.pooler.supabase.com:5432", url)
    
    # 2b. Fallback to env var or default for project ref
    if not project_ref:
        env_ref = os.getenv("SUPABASE_PROJECT_REF", "").strip()
        project_ref = env_ref if env_ref else "jddyiqdllaytbhopjmch"

    # 2c. Ensure tenant identifier (.project_ref) is present in username for pooler
    if "pooler.supabase.com" in url:
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
            url = url[:user_pass_match.start(1)] + new_user_pass + url[user_pass_match.end(1):]
    
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
    db = None
    try:
        db = SessionLocal()
        # Probe connection
        db.connection()
        yield db
    except Exception as e:
        print(f"⚠️ Primary DB connection error: {e}. Falling back to SQLite.")
        if db:
            try:
                db.close()
            except Exception:
                pass
        fallback_engine = create_engine("sqlite:///./veritas.db", connect_args={"check_same_thread": False})
        from . import models  # noqa: F401
        Base.metadata.create_all(bind=fallback_engine)
        FallbackSession = sessionmaker(autocommit=False, autoflush=False, bind=fallback_engine)
        db = FallbackSession()
        try:
            yield db
        finally:
            db.close()
    finally:
        if db:
            try:
                db.close()
            except Exception:
                pass


def init_db():
    """Create all tables defined in models.py. Called once at startup."""
    try:
        from . import models  # noqa: F401 — ensure models are registered
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"⚠️ Note: Database auto-creation notice ({e}). Continuing startup...")
