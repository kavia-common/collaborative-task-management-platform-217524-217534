from os import getenv

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TaskBoards Backend",
    description="API for TaskBoards: projects, boards, tasks, tags, and realtime collaboration.",
    version="0.1.0",
    contact={"name": "TaskBoards"},
    license_info={"name": "MIT"},
    openapi_tags=[
        {"name": "health", "description": "Service health and diagnostics"},
    ],
)

# CORS configuration from environment
cors_origins_raw = getenv("CORS_ALLOW_ORIGINS", "*")
allow_origins = [o.strip() for o in cors_origins_raw.split(",")] if cors_origins_raw else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins if allow_origins != [""] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON payload indicating service health.
    """
    return {"message": "Healthy"}
