import os
from functools import lru_cache
from typing import List


class Settings:
    """
    Application settings loaded from environment variables.

    Environment variables:
    - SECRET_KEY: secret for signing JWT tokens (recommended; required for auth)
    - ACCESS_TOKEN_EXPIRE_MINUTES: token expiration in minutes (default: 60)
    - CORS_ALLOW_ORIGINS: comma-separated list of allowed origins (default: *)
    - DATABASE_URL: SQLAlchemy connection URL (optional for startup)
    """

    def __init__(self) -> None:
        # Do not raise at import/startup; allow app to boot without SECRET_KEY for health/status
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
        self.CORS_ALLOW_ORIGINS: List[str] = [o.strip() for o in cors_raw.split(",")] if cors_raw else ["*"]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    PUBLIC_INTERFACE
    Return cached Settings instance loaded from environment.
    """
    return Settings()
