"""
database.py
-----------
Phase 3: SQLAlchemy engine + session factory.

DATABASE_URL defaults to SQLite (zero-setup for local dev).
Swap in Postgres for production by setting the env var:
    DATABASE_URL=postgresql://user:pass@host:5432/veritas

The schema stays the same — all JSON columns, no over-normalization for MVP.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./veritas.db")

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
