import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Create the declarative base for models
Base = declarative_base()

# Lazy-singletons for engine and session factory
_engine = None
_SessionLocal: Optional[sessionmaker] = None


def _get_database_url() -> Optional[str]:
    """
    Resolve DATABASE_URL from environment variables.

    Returns:
        The connection URL if present; otherwise None. Supports Postgres via psycopg.
    """
    return os.getenv("DATABASE_URL")


def _init_engine_and_session() -> None:
    """
    Initialize the SQLAlchemy engine and session factory lazily.
    Does nothing if DATABASE_URL is not provided.
    """
    global _engine, _SessionLocal
    if _engine is not None and _SessionLocal is not None:
        return
    url = _get_database_url()
    if not url:
        # Defer configuration; routes will guard via get_db()
        return
    _engine = create_engine(
        url,
        pool_pre_ping=True,  # proactively ping connections
        future=True,
    )
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine,
        class_=Session,
        future=True,
    )


# PUBLIC_INTERFACE
def is_db_configured() -> bool:
    """
    Return True if DATABASE_URL is present and the engine/session can be initialized.
    Note: This does not attempt to connect to the DB, only checks configuration presence.
    """
    if _get_database_url():
        # Try initializing if not already
        _init_engine_and_session()
        return _SessionLocal is not None
    return False


def get_sessionmaker() -> Optional[sessionmaker]:
    """
    Return the configured Session maker if available, otherwise None.
    """
    _init_engine_and_session()
    return _SessionLocal


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session for FastAPI dependency injection and ensure cleanup.

    Behavior when DB is not configured:
    - If called within FastAPI request context, raises HTTP 503 so routes respond gracefully.
    - If used outside FastAPI (e.g., scripts), raises RuntimeError with guidance.
    """
    # Import lazily to avoid import-time dependency on FastAPI
    try:
        from fastapi import HTTPException, status
    except Exception:
        # Not in a FastAPI runtime (or FastAPI unavailable): raise descriptive error if unconfigured
        if not is_db_configured():
            raise RuntimeError(
                "Database not configured. Set DATABASE_URL. See .env.example and taskboards_backend/SETUP_DB.md"
            )
        SessionLocal = get_sessionmaker()
        assert SessionLocal is not None
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
        return

    if not is_db_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set DATABASE_URL. See .env.example",
        )

    SessionLocal = get_sessionmaker()
    assert SessionLocal is not None
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
    if not is_db_configured():
        raise RuntimeError("Database not configured. Set DATABASE_URL. See .env.example")
    SessionLocal = get_sessionmaker()
    assert SessionLocal is not None
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
