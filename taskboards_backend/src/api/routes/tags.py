from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db import get_db
from src.db.models import Project, Tag, User
from src.db.schemas import TagCreate, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


def _assert_project_access(db: Session, project_id: int, user_id: int) -> None:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")


@router.post("", summary="Create tag", response_model=TagOut, status_code=201)
def create_tag(body: TagCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> TagOut:
    _assert_project_access(db, body.project_id, user.id)
    tag = Tag(project_id=body.project_id, name=body.name, color=body.color)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@router.get("/project/{project_id}", summary="List tags by project", response_model=List[TagOut])
def list_tags(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> List[TagOut]:
    _assert_project_access(db, project_id, user.id)
    return db.query(Tag).filter(Tag.project_id == project_id).order_by(Tag.name.asc()).all()


@router.delete("/{tag_id}", summary="Delete tag", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    _assert_project_access(db, tag.project_id, user.id)
    db.delete(tag)
    db.commit()
    return None
