from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db import get_db
from src.db.models import Assignment, BoardColumn, Project, Tag, Task, TaskTag, User
from src.db.schemas import TaskCreate, TaskOut, TaskUpdate
from src.services.task_service import TaskFilters, filter_tasks

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _project_check(db: Session, project_id: int, user_id: int) -> None:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("", summary="Create task", response_model=TaskOut, status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskOut:
    _project_check(db, body.project_id, user.id)
    if body.column_id:
        col = db.query(BoardColumn).filter(BoardColumn.id == body.column_id, BoardColumn.project_id == body.project_id).first()
        if not col:
            raise HTTPException(status_code=400, detail="Column does not belong to project")
    task = Task(
        project_id=body.project_id,
        column_id=body.column_id,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=body.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", summary="Get task", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskOut:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _project_check(db, task.project_id, user.id)
    return task


@router.put("/{task_id}", summary="Update task", response_model=TaskOut)
def update_task(task_id: int, body: TaskUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskOut:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _project_check(db, task.project_id, user.id)
    if body.column_id is not None:
        if body.column_id:
            col = db.query(BoardColumn).filter(BoardColumn.id == body.column_id, BoardColumn.project_id == task.project_id).first()
            if not col:
                raise HTTPException(status_code=400, detail="Column does not belong to project")
        task.column_id = body.column_id
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    if body.priority is not None:
        task.priority = body.priority
    if body.due_date is not None:
        task.due_date = body.due_date
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", summary="Delete task", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _project_check(db, task.project_id, user.id)
    db.delete(task)
    db.commit()
    return None


@router.get("", summary="List tasks with filters", response_model=List[TaskOut])
def list_tasks(
    projectId: Optional[int] = Query(None, description="Project ID"),
    tags: Optional[str] = Query(None, description="Comma-separated tag ids"),
    assigneeId: Optional[int] = Query(None, description="Assignee user id"),
    priority: Optional[int] = Query(None, description="Priority 1-5"),
    status: Optional[int] = Query(None, description="Column id for status"),
    dueFrom: Optional[datetime] = Query(None, description="Due date from"),
    dueTo: Optional[datetime] = Query(None, description="Due date to"),
    search: Optional[str] = Query(None, description="Text search"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[TaskOut]:
    """
    Filter tasks by multiple criteria.
    """
    if projectId is not None:
        _project_check(db, projectId, user.id)
    tag_ids = [int(t) for t in tags.split(",")] if tags else None
    filters = TaskFilters(
        project_id=projectId,
        tag_ids=tag_ids,
        assignee_id=assigneeId,
        priority=priority,
        due_from=dueFrom,
        due_to=dueTo,
        search=search,
        status_column_id=status,
    )
    tasks = filter_tasks(db, filters)
    return tasks


class TaskTagUpdate(BaseModel):
    tag_ids: List[int] = Field(default_factory=list, description="New set of tag ids for task")


@router.put("/{task_id}/tags", summary="Replace task tags", response_model=TaskOut)
def replace_task_tags(task_id: int, body: TaskTagUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskOut:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _project_check(db, task.project_id, user.id)
    # Validate tags belong to same project
    if body.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in__(body.tag_ids), Tag.project_id == task.project_id).all()
        if len(tags) != len(set(body.tag_ids)):
            raise HTTPException(status_code=400, detail="One or more tags invalid for this project")
    # Clear then add
    db.query(TaskTag).filter(TaskTag.task_id == task.id).delete()
    for tag_id in set(body.tag_ids):
        db.add(TaskTag(task_id=task.id, tag_id=tag_id))
    db.commit()
    db.refresh(task)
    return task


class AssignmentUpdate(BaseModel):
    user_ids: List[int] = Field(default_factory=list, description="Replace assignees with these user ids")


@router.put("/{task_id}/assignees", summary="Replace task assignees", response_model=TaskOut)
def replace_assignees(task_id: int, body: AssignmentUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TaskOut:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _project_check(db, task.project_id, user.id)
    # Replace
    db.query(Assignment).filter(Assignment.task_id == task.id).delete()
    for uid in set(body.user_ids):
        db.add(Assignment(user_id=uid, task_id=task.id))
    db.commit()
    db.refresh(task)
    return task
