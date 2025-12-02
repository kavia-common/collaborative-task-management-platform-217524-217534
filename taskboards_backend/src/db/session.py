import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Create the declarative base for models
Base = declarative_base()


def _get_database_url() -> str:
    """
    Resolve DATABASE_URL from environment variables.
    Supports Postgres via psycopg.
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        # Note: Do not hardcode credentials; require env configuration.
        raise RuntimeError(
            "DATABASE_URL environment variable is required. "
            "See .env.example for the expected format."
        )
    return url


# Configure SQLAlchemy engine and session factory
DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(
    _get_database_url(),
    pool_pre_ping=True,  # proactively ping connections
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
    future=True,
)


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session for FastAPI dependency injection and ensure cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for application code outside FastAPI dependencies.

    Example:
        with db_session() as db:
            db.query(Model).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
