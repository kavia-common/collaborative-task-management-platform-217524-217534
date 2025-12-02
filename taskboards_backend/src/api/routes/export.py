from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db import get_db
from src.db.models import Project, User
from src.services.task_service import TaskFilters, filter_tasks
from src.services.export_service import tasks_to_csv

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/tasks", summary="Export tasks to CSV")
def export_tasks_csv(
    projectId: int = Query(..., description="Project ID to export"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Export tasks for a project as CSV.
    """
    project = db.query(Project).filter(Project.id == projectId, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks = filter_tasks(db, TaskFilters(project_id=projectId))
    csv_bytes = tasks_to_csv(tasks)
    headers = {
        "Content-Disposition": f'attachment; filename="project_{projectId}_tasks.csv"'
    }
    return Response(content=csv_bytes, headers=headers, media_type="text/csv")
