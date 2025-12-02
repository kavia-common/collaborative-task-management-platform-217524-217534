import os
from functools import lru_cache
from typing import List

from src.core.diagnostics import parse_cors_and_ws_from_env


class Settings:
    """
    Application settings loaded from environment variables.

    Environment variables:
    - SECRET_KEY: secret for signing JWT tokens (recommended; required for auth)
    - ACCESS_TOKEN_EXPIRE_MINUTES: token expiration in minutes (default: 60)
    - CORS_ALLOW_ORIGINS: comma-separated list of allowed origins (default: *)
    - WEBSOCKET_ORIGINS: optional comma-separated list of allowed websocket origins
    - DATABASE_URL: SQLAlchemy connection URL (optional for startup)
    """

    def __init__(self) -> None:
        # Do not raise at import/startup; allow app to boot without SECRET_KEY for health/status
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        cors_ws = parse_cors_and_ws_from_env()
        self.CORS_ALLOW_ORIGINS: List[str] = cors_ws["cors"] or ["*"]
        self.WEBSOCKET_ORIGINS: List[str] = cors_ws["ws"] or self.CORS_ALLOW_ORIGINS


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    PUBLIC_INTERFACE
    Return cached Settings instance loaded from environment.
    """
    return Settings()
