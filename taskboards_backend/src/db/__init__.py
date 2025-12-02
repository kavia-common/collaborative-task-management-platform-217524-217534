"""
Database package initialization for TaskBoards backend.

Exposes:
- Base: SQLAlchemy declarative base for model definitions.
- get_db: PUBLIC_INTERFACE FastAPI dependency for DB sessions.
"""

from .session import Base, get_db

__all__ = ["Base", "get_db"]
