from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.api.routes.auth import router as auth_router
from src.api.routes.projects import router as projects_router
from src.api.routes.columns import router as columns_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.tags import router as tags_router
from src.api.routes.export import router as export_router
from src.core.config import get_settings
from src.core.diagnostics import (
    attach_request_logging_middleware,
    build_status_payload,
    log_event,
    make_logger,
)
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

# Load settings and logger
settings = get_settings()
app_logger = make_logger("taskboards.app")

# CORS using settings (improved parsing is handled in settings)
allow_origins: List[str] = settings.CORS_ALLOW_ORIGINS or ["*"]
log_event(app_logger, "cors_configuration", allow_origins=allow_origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight request logging middleware
app.middleware("http")(attach_request_logging_middleware(app_logger))


@app.on_event("startup")
def _startup_check() -> None:
    """
    Startup diagnostics. Warn if DATABASE_URL is missing rather than crashing.
    """
    try:
        if not is_db_configured():
            log_event(
                app_logger,
                "db_unconfigured",
                message="DATABASE_URL not configured. DB-backed endpoints will return 503 until configured.",
            )
    except Exception:
        # Do not block startup for any reason
        pass


@app.get("/", tags=["health"], summary="Health Check", description="Simple health check endpoint.")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON payload indicating service health.
    """
    return {"message": "Healthy"}


class StatusResponse(BaseModel):
    app_version: str = Field(..., description="Application version")
    db_configured: bool = Field(..., description="True if DATABASE_URL is present")
    secret_key_configured: bool = Field(..., description="True if SECRET_KEY is present")
    cors_origins: List[str] = Field(..., description="Effective CORS allow origins")
    websocket_origins: List[str] = Field(..., description="Effective WebSocket allow origins")
    uptime_seconds: int = Field(..., description="Seconds since process start")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal startup/runtime warnings")


@app.get(
    "/status",
    tags=["health"],
    summary="Runtime status",
    description=(
        "Report runtime configuration status including app version, DB and secret key presence, "
        "effective CORS/WebSocket origins, uptime, and warnings. This endpoint never requires DB."
    ),
    response_model=StatusResponse,
    responses={
        200: {"description": "Current runtime status"},
    },
)
def runtime_status():
    """
    Return runtime configuration and diagnostics.

    Returns:
        StatusResponse JSON with fields suitable for frontend onboarding.
    """
    warnings: List[str] = []
    if not is_db_configured():
        warnings.append("DATABASE_URL is not configured. DB-backed routes will return 503.")
    if not settings.SECRET_KEY:
        warnings.append("SECRET_KEY is not configured. Auth routes will return 503.")
    payload = build_status_payload(
        app_version=app.version,
        db_configured=is_db_configured(),
        secret_key_configured=bool(settings.SECRET_KEY),
        cors_origins=settings.CORS_ALLOW_ORIGINS or ["*"],
        websocket_origins=getattr(settings, "WEBSOCKET_ORIGINS", settings.CORS_ALLOW_ORIGINS) or ["*"],
        warnings=warnings,
    )
    return JSONResponse(payload)


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
