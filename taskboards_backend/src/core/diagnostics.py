import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from fastapi import Request
from starlette.responses import JSONResponse

# Global process start time for uptime calculations
_PROCESS_START_TIME = time.time()


def _parse_csv_env(name: str, default: Optional[List[str]] = None) -> List[str]:
    """
    Parse a comma-separated environment variable into a list of trimmed strings.
    Empty or missing values return the provided default or [].
    """
    raw = os.getenv(name, "")
    if not raw:
        return default[:] if default is not None else []
    # split and strip, drop empty segments
    parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p]


def _bool_env(name: str, default: bool = False) -> bool:
    """
    Parse boolean-ish environment variables.
    """
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "y", "on"}


# PUBLIC_INTERFACE
def build_status_payload(
    *,
    app_version: str,
    db_configured: bool,
    secret_key_configured: bool,
    cors_origins: List[str],
    websocket_origins: List[str],
    warnings: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build the status JSON payload with runtime diagnostics."""
    uptime = max(0, time.time() - _PROCESS_START_TIME)
    return {
        "app_version": app_version,
        "db_configured": bool(db_configured),
        "secret_key_configured": bool(secret_key_configured),
        "cors_origins": cors_origins,
        "websocket_origins": websocket_origins,
        "uptime_seconds": int(uptime),
        "warnings": warnings or [],
    }


# PUBLIC_INTERFACE
def db_unavailable_response(details: Optional[str] = None) -> JSONResponse:
    """
    Return a standardized 503 response body for endpoints that require the DB.
    Includes actionable hints for configuration.
    """
    message = details or "Database not configured. Set DATABASE_URL. See .env.example and SETUP_DB.md"
    hints = [
        "Set DATABASE_URL environment variable to a valid SQLAlchemy URL.",
        "See taskboards_backend/SETUP_DB.md for instructions.",
        "After setting DATABASE_URL, run Alembic migrations: alembic upgrade head",
        "Restart the backend service after configuration.",
    ]
    body = {
        "error": "service_unavailable",
        "message": message,
        "action_hints": hints,
    }
    return JSONResponse(status_code=503, content=body)


# PUBLIC_INTERFACE
def make_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Create a simple structured logger with JSON-ish formatting for key events.
    Level can be overridden via level param or LOG_LEVEL env variable.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    env_level = (level or os.getenv("LOG_LEVEL") or "INFO").upper()
    logger.setLevel(env_level)
    return logger


# PUBLIC_INTERFACE
def log_event(logger: logging.Logger, event: str, **fields: Any) -> None:
    """
    Emit a lightweight structured log line as a JSON string with an 'event' key.
    """
    try:
        payload = {"event": event, **fields}
        logger.info(json.dumps(payload, separators=(",", ":")))
    except Exception:
        # Fallback to plain logging if serialization fails
        logger.info(f"event={event} fields={fields}")


# PUBLIC_INTERFACE
def parse_cors_and_ws_from_env() -> Dict[str, List[str]]:
    """
    Parse CORS and WebSocket allowed origins from environment.

    Env:
      - CORS_ALLOW_ORIGINS: comma-separated list; '*' allowed
      - WEBSOCKET_ORIGINS: optional comma-separated list; fallback to CORS origins when missing
    """
    cors = _parse_csv_env("CORS_ALLOW_ORIGINS", default=["*"]) or ["*"]
    ws = _parse_csv_env("WEBSOCKET_ORIGINS", default=cors)
    return {"cors": cors, "ws": ws}


# PUBLIC_INTERFACE
def attach_request_logging_middleware(app_logger: logging.Logger):
    """
    Return a simple middleware function to log basic request info without heavy overhead.
    """

    async def logger_middleware(request: Request, call_next):
        # Only log small set of info for brevity
        start = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        log_event(
            app_logger,
            "http_request",
            method=request.method,
            path=request.url.path,
            status=getattr(response, "status_code", 0),
            duration_ms=duration_ms,
        )
        return response

    return logger_middleware
