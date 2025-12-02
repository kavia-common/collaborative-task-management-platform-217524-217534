# TaskBoards Backend Status Endpoint

## Overview

The TaskBoards backend exposes a diagnostics endpoint at GET /status that reports runtime configuration health. This endpoint never requires the database and is safe to call at all times, including during initial setup or incidents. It is used by the frontend developer diagnostics panel and is intended to help operators complete configuration and troubleshoot common issues quickly.

## Endpoint

- Method and path: GET /status
- Authentication: None
- Returns: 200 OK with JSON payload

## Response Fields

- app_version: The current application version string (for example, "0.1.0").
- db_configured: True when DATABASE_URL is present so DB-backed endpoints can operate; false otherwise.
- secret_key_configured: True when SECRET_KEY is set so authentication can operate; false otherwise.
- cors_origins: The effective list of HTTP CORS allow origins. Values come from CORS_ALLOW_ORIGINS and support comma-separated lists; whitespace is trimmed. An asterisk (*) allows all origins.
- websocket_origins: The effective list of WebSocket origins. Values come from WEBSOCKET_ORIGINS; when that is not set, it falls back to cors_origins.
- uptime_seconds: The number of seconds since the backend process started.
- warnings: A list of non-fatal configuration warnings. When DATABASE_URL or SECRET_KEY is missing, warnings will include actionable messages.

## Example Responses

Minimal configuration (local):
{
  "app_version": "0.1.0",
  "db_configured": false,
  "secret_key_configured": false,
  "cors_origins": ["http://localhost:3000"],
  "websocket_origins": ["http://localhost:3000"],
  "uptime_seconds": 7,
  "warnings": [
    "DATABASE_URL is not configured. DB-backed routes will return 503.",
    "SECRET_KEY is not configured. Auth routes will return 503."
  ]
}

Configured for two frontend origins:
{
  "app_version": "0.1.0",
  "db_configured": true,
  "secret_key_configured": true,
  "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
  "websocket_origins": ["http://localhost:3000", "http://localhost:5173"],
  "uptime_seconds": 124,
  "warnings": []
}

Wildcard CORS (not recommended for production):
{
  "app_version": "0.1.0",
  "db_configured": true,
  "secret_key_configured": true,
  "cors_origins": ["*"],
  "websocket_origins": ["*"],
  "uptime_seconds": 314,
  "warnings": []
}

## How to Use /status for Troubleshooting

- Database unavailable (db_configured=false):
  - Set DATABASE_URL to a valid SQLAlchemy connection URL.
  - Run migrations: alembic upgrade head.
  - Restart the backend.
  - See taskboards_backend/SETUP_DB.md for detailed steps and example commands.
- Secret key missing (secret_key_configured=false):
  - Set SECRET_KEY to a strong, non-empty value.
  - Restart the backend.
- CORS complaints in browser console or blocked API calls:
  - Ensure your frontend origin is listed in cors_origins.
  - For multiple dev origins, set a comma-separated list in CORS_ALLOW_ORIGINS:
    CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
  - Restart the backend and observe startup logs for "cors_configuration" to confirm the effective origins.
- WebSocket connection failing:
  - If you use a distinct WS origin or scheme, set WEBSOCKET_ORIGINS accordingly:
    WEBSOCKET_ORIGINS=http://localhost:3000,https://example.com
  - When WEBSOCKET_ORIGINS is not set, websocket_origins defaults to the same list as cors_origins.

## CORS Configuration Guidance

- CORS_ALLOW_ORIGINS supports comma-separated lists. Whitespace is trimmed and empty segments are ignored.
- An asterisk (*) allows requests from all origins. This is convenient for early development but should be avoided in production.
- WEBSOCKET_ORIGINS is optional; when omitted, it falls back to CORS_ALLOW_ORIGINS. Provide it if your WebSocket deployment constraints differ from HTTP requests.

Examples:
- Single origin:
  CORS_ALLOW_ORIGINS=http://localhost:3000
- Multiple origins (comma-separated):
  CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
- Distinct WebSocket origins:
  CORS_ALLOW_ORIGINS=https://app.example.com
  WEBSOCKET_ORIGINS=https://ws.example.com

## References

- Source files:
  - taskboards_backend/src/api/main.py
  - taskboards_backend/src/core/config.py
  - taskboards_backend/src/core/diagnostics.py
- Database setup guide:
  - taskboards_backend/SETUP_DB.md
