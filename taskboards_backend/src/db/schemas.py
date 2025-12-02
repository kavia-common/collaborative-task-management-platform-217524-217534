from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# Base reusable models
class Timestamped(BaseModel):
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp (UTC) if applicable")


# User Schemas
class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    name: Optional[str] = Field(None, description="Display name")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plain password to be hashed")


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Display name to update")
    password: Optional[str] = Field(None, min_length=8, description="New password")


class UserOut(UserBase, Timestamped):
    id: int = Field(..., description="User identifier")
    is_active: bool = Field(..., description="Active status")

    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Project name")
    description: Optional[str] = Field(None, description="Project description")


class ProjectOut(ProjectBase, Timestamped):
    id: int = Field(..., description="Project identifier")
    owner_id: int = Field(..., description="Owner (user) id")

    class Config:
        from_attributes = True


# Column Schemas
class ColumnBase(BaseModel):
    name: str = Field(..., max_length=100, description="Column name")
    order_index: int = Field(0, ge=0, description="Ordering index within the project")


class ColumnCreate(ColumnBase):
    project_id: int = Field(..., description="Project identifier")


class ColumnUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Column name")
    order_index: Optional[int] = Field(None, ge=0, description="Ordering index within the project")


class ColumnOut(ColumnBase):
    id: int = Field(..., description="Column identifier")
    project_id: int = Field(..., description="Project identifier")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")

    class Config:
        from_attributes = True


# Tag Schemas
class TagBase(BaseModel):
    name: str = Field(..., max_length=50, description="Tag name")
    color: Optional[str] = Field(None, description="Hex color like #RRGGBB")


class TagCreate(TagBase):
    project_id: int = Field(..., description="Project identifier")


class TagOut(TagBase):
    id: int = Field(..., description="Tag identifier")
    project_id: int = Field(..., description="Project identifier")

    class Config:
        from_attributes = True


# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., max_length=255, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: int = Field(3, ge=1, le=5, description="Priority from 1 (high) to 5 (low)")
    due_date: Optional[datetime] = Field(None, description="Due date")


class TaskCreate(TaskBase):
    project_id: int = Field(..., description="Project identifier")
    column_id: Optional[int] = Field(None, description="Column identifier")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: Optional[int] = Field(None, ge=1, le=5, description="Priority 1-5")
    due_date: Optional[datetime] = Field(None, description="Due date")
    column_id: Optional[int] = Field(None, description="Column identifier")


class TaskOut(TaskBase):
    id: int = Field(..., description="Task identifier")
    project_id: int = Field(..., description="Project identifier")
    column_id: Optional[int] = Field(None, description="Column identifier")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")
    tags: List[TagOut] = Field(default_factory=list, description="Tags for the task")

    class Config:
        from_attributes = True


# Assignment Schemas
class AssignmentCreate(BaseModel):
    user_id: int = Field(..., description="User identifier")
    task_id: int = Field(..., description="Task identifier")


class AssignmentOut(BaseModel):
    user_id: int = Field(..., description="User identifier")
    task_id: int = Field(..., description="Task identifier")
    assigned_at: datetime = Field(..., description="Assignment timestamp")

    class Config:
        from_attributes = True


# Activity Schemas
class ActivityCreate(BaseModel):
    task_id: int = Field(..., description="Task identifier")
    action: str = Field(..., max_length=100, description="Type of action")
    # Note: This maps to DB column 'metadata' via ORM attribute Activity.meta_json
    meta_json: Optional[str] = Field(None, description="Optional metadata JSON")


class ActivityOut(BaseModel):
    id: int = Field(..., description="Activity identifier")
    task_id: int = Field(..., description="Task identifier")
    actor_id: int = Field(..., description="Actor (user) identifier")
    action: str = Field(..., description="Type of action")
    # Note: Exposes ORM attribute 'meta_json' which maps to DB 'metadata'
    meta_json: Optional[str] = Field(None, description="Optional metadata JSON")
    created_at: datetime = Field(..., description="Timestamp")

    class Config:
        from_attributes = True
