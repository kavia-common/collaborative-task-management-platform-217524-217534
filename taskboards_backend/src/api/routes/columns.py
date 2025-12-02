from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db import get_db
from src.db.models import BoardColumn, Project, User
from src.db.schemas import ColumnCreate, ColumnOut, ColumnUpdate

router = APIRouter(prefix="/columns", tags=["columns"])


def _ensure_project_access(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("", summary="Create column", response_model=ColumnOut, status_code=201)
def create_column(body: ColumnCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ColumnOut:
    _ensure_project_access(db, body.project_id, user.id)
    col = BoardColumn(project_id=body.project_id, name=body.name, order_index=body.order_index)
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.get("/project/{project_id}", summary="List columns by project", response_model=List[ColumnOut])
def list_columns(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> List[ColumnOut]:
    _ensure_project_access(db, project_id, user.id)
    return db.query(BoardColumn).filter(BoardColumn.project_id == project_id).order_by(BoardColumn.order_index.asc()).all()


@router.put("/{column_id}", summary="Update column", response_model=ColumnOut)
def update_column(column_id: int, body: ColumnUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ColumnOut:
    col = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    _ensure_project_access(db, col.project_id, user.id)
    if body.name is not None:
        col.name = body.name
    if body.order_index is not None:
        col.order_index = body.order_index
    db.add(col)
    db.commit()
    db.refresh(col)
    return col


@router.delete("/{column_id}", summary="Delete column", status_code=204)
def delete_column(column_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    col = db.query(BoardColumn).filter(BoardColumn.id == column_id).first()
    if not col:
        raise HTTPException(status_code=404, detail="Column not found")
    _ensure_project_access(db, col.project_id, user.id)
    db.delete(col)
    db.commit()
    return None
