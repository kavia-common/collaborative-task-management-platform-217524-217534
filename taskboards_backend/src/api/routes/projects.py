from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user
from src.db import get_db
from src.db.models import Project, User
from src.db.schemas import ProjectCreate, ProjectOut, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", summary="List projects for current user", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> List[ProjectOut]:
    """
    Get all projects owned by the current user.
    """
    return db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()


@router.post("", summary="Create a project", response_model=ProjectOut, status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectOut:
    """
    Create a project owned by current user.
    """
    exists = db.query(Project).filter(Project.owner_id == user.id, Project.name == body.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Project with same name already exists")
    project = Project(name=body.name, description=body.description, owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", summary="Get a project", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectOut:
    """
    Retrieve a single project by id (must be owned by current user).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", summary="Update a project", response_model=ProjectOut)
def update_project(project_id: int, body: ProjectUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> ProjectOut:
    """
    Update project fields (name, description).
    """
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if body.name is not None:
        # ensure unique per owner
        dup = db.query(Project).filter(Project.owner_id == user.id, Project.name == body.name, Project.id != project_id).first()
        if dup:
            raise HTTPException(status_code=400, detail="Another project with the same name exists")
        project.name = body.name
    if body.description is not None:
        project.description = body.description
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", summary="Delete a project", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> None:
    """
    Delete a project owned by current user.
    """
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
