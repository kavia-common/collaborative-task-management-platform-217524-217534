# collaborative-task-management-platform-217524-217534

This project includes a TaskBoards backend (FastAPI) and a React frontend.

Backend quick start:
- The backend defers database initialization until runtime. If DATABASE_URL is not set, DB-backed endpoints return 503, but the app starts and health endpoints work.
- See taskboards_backend/SETUP_DB.md for instructions to configure DATABASE_URL and run Alembic migrations.
- Copy taskboards_backend/.env.example to .env and fill required values.

Health endpoints:
- GET /          -> {"message":"Healthy"}
- GET /status    -> {
    "app_version": "0.1.0",
    "db_configured": true|false,
    "secret_key_configured": true|false,
    "cors_origins": ["*"] or ["http://localhost:3000", ...],
    "websocket_origins": [...],
    "uptime_seconds": <int>,
    "warnings": [ ... ]
  }