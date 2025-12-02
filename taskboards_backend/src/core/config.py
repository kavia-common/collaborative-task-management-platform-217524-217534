import os
from functools import lru_cache
from typing import List


class Settings:
    """
    Application settings loaded from environment variables.

    Environment variables:
    - SECRET_KEY: secret for signing JWT tokens (required)
    - ACCESS_TOKEN_EXPIRE_MINUTES: token expiration in minutes (default: 60)
    - CORS_ALLOW_ORIGINS: comma-separated list of allowed origins (default: *)
    - DATABASE_URL: SQLAlchemy connection URL (required, configured elsewhere)
    """

    def __init__(self) -> None:
        self.SECRET_KEY: str = os.getenv("SECRET_KEY", "")
        self.ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "*")
        self.CORS_ALLOW_ORIGINS: List[str] = [o.strip() for o in cors_raw.split(",")] if cors_raw else ["*"]

        # Validate critical settings
        if not self.SECRET_KEY:
            # We do not hardcode; CI/Runtime must provide.
            # Raising a RuntimeError makes issues explicit at startup.
            raise RuntimeError(
                "SECRET_KEY environment variable is required for JWT signing. "
                "Please configure it in the .env file."
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    PUBLIC_INTERFACE
    Return cached Settings instance loaded from environment.
    """
    return Settings()
