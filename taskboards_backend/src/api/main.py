from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes.auth import router as auth_router
from src.api.routes.projects import router as projects_router
from src.api.routes.columns import router as columns_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.tags import router as tags_router
from src.api.routes.export import router as export_router
from src.core.config import get_settings
from src.realtime.manager import ConnectionManager
from src.db.session import is_db_configured

openapi_tags = [
    {"name": "health", "description": "Service health and diagnostics"},
    {"name": "auth", "description": "Authentication (register/login)"},
    {"name": "projects", "description": "Project management"},
    {"name": "columns", "description": "Kanban board columns"},
    {"name": "tasks", "description": "Tasks CRUD and filters"},
    {"name": "tags", "description": "Tags management"},
    {"name": "export", "description": "CSV exports"},
    {"name": "realtime", "description": "WebSocket realtime events"},
]

app = FastAPI(
    title="TaskBoards Backend",
    description="API for TaskBoards: projects, boards, tasks, tags, and realtime collaboration.",
    version="0.1.0",
    contact={"name": "TaskBoards"},
    license_info={"name": "MIT"},
    openapi_tags=openapi_tags,
)

# Load settings to validate env and to get CORS
settings = get_settings()

# CORS using settings
allow_origins = settings.CORS_ALLOW_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != [""] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup_check() -> None:
    """
    Startup diagnostics. Warn if DATABASE_URL is missing rather than crashing.
    """
    try:
        if not is_db_configured():
            # Log a warning; app still starts so health endpoint works
            app.logger and app.logger.warning(
                "DATABASE_URL not configured. DB-backed endpoints will return 503 until configured. "
                "See .env.example and SETUP_DB.md"
            )
    except Exception:
        # Do not block startup for any reason
        pass


@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON payload indicating service health.
    """
    return {"message": "Healthy"}


@app.get("/status", tags=["health"], summary="Runtime status")
def runtime_status():
    """
    Report runtime configuration status.

    Returns:
        JSON with dbConfigured: true|false so frontends can drive onboarding.
    """
    return JSONResponse({"dbConfigured": bool(is_db_configured())})


# Include API routers
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(columns_router)
app.include_router(tasks_router)
app.include_router(tags_router)
app.include_router(export_router)

# WebSocket manager
ws_manager = ConnectionManager()


@app.websocket("/ws/projects/{project_id}")
async def project_ws(websocket: WebSocket, project_id: int):
    """
    WebSocket realtime channel for a project.

    Usage:
      Connect to /ws/projects/{project_id}.
      Messages are JSON with fields:
        - type: event type, e.g. "task.created", "presence.join"
        - payload: optional data

    This endpoint broadcasts received payloads to all peers in the same project room.

    Security:
      This channel is unauthenticated for simplicity of demo, but should be upgraded to JWT-based auth headers/cookies in production.
    """
    room = f"project:{project_id}"
    await ws_manager.connect(room, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # broadcast as received
            await ws_manager.broadcast(room, data)
    except WebSocketDisconnect:
        await ws_manager.disconnect(room, websocket)
