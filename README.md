# collaborative-task-management-platform-217524-217534

This project includes a TaskBoards backend (FastAPI) and a React frontend.

Backend quick start:
- The backend defers database initialization until runtime. If DATABASE_URL is not set, DB-backed endpoints return 503, but the app starts and health endpoints work.
- See taskboards_backend/SETUP_DB.md for instructions to configure DATABASE_URL and run Alembic migrations.
- Copy taskboards_backend/.env.example to .env and fill required values.

Health endpoints:
- GET / -> {"message":"Healthy"}
- GET /status -> runtime diagnostics JSON; see details below.

Status endpoint details:
/status returns a structured JSON payload to help operators and the frontend verify configuration. It never requires a database.

Fields:
- app_version: Application version string, e.g., "0.1.0"
- db_configured: true if DATABASE_URL is present (DB-backed routes will work), false otherwise
- secret_key_configured: true if SECRET_KEY is present (auth routes will work), false otherwise
- cors_origins: Effective list of HTTP CORS origins (derived from CORS_ALLOW_ORIGINS, supports comma-separated values)
- websocket_origins: Effective list of WebSocket origins (derived from WEBSOCKET_ORIGINS or falls back to CORS origins)
- uptime_seconds: Seconds since process start
- warnings: Non-fatal configuration warnings (e.g., missing DATABASE_URL or SECRET_KEY)

Example response:
{
  "app_version": "0.1.0",
  "db_configured": false,
  "secret_key_configured": false,
  "cors_origins": ["http://localhost:3000"],
  "websocket_origins": ["http://localhost:3000"],
  "uptime_seconds": 12,
  "warnings": [
    "DATABASE_URL is not configured. DB-backed routes will return 503.",
    "SECRET_KEY is not configured. Auth routes will return 503."
  ]
}

Troubleshooting using /status:
- If db_configured=false, set DATABASE_URL and run Alembic migrations (see taskboards_backend/SETUP_DB.md), then restart the backend.
- If secret_key_configured=false, set SECRET_KEY to a strong value and restart.
- If the frontend cannot connect due to CORS, verify cors_origins includes your frontend origin. For local dev, set:
  CORS_ALLOW_ORIGINS=http://localhost:3000
- For multiple origins, provide a comma-separated list:
  CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:5173
- If websockets are blocked, set WEBSOCKET_ORIGINS (comma-separated). If omitted, it falls back to CORS_ALLOW_ORIGINS.

CORS configuration notes:
- CORS_ALLOW_ORIGINS accepts comma-separated values; whitespace is trimmed. An asterisk (*) allows all origins.
- WEBSOCKET_ORIGINS is optional. When not set, the backend uses the same list as CORS_ALLOW_ORIGINS.
- The backend logs effective CORS origins on startup for visibility.

For database setup and structured 503 responses when DB is unavailable, see taskboards_backend/SETUP_DB.md.