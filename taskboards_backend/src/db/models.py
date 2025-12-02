from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="owner", cascade="all,delete-orphan"
    )
    assignments: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="user", cascade="all,delete-orphan"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="actor", cascade="all,delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    owner: Mapped["User"] = relationship("User", back_populates="projects")
    columns: Mapped[List["BoardColumn"]] = relationship(
        "BoardColumn", back_populates="project", cascade="all,delete-orphan", order_by="BoardColumn.order_index"
    )
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", back_populates="project", cascade="all,delete-orphan"
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all,delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_project_owner_name"),
        Index("ix_project_owner", "owner_id"),
    )


class BoardColumn(Base):
    __tablename__ = "columns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="columns")
    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="column", cascade="all,delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_column_project_name"),
        Index("ix_column_project", "project_id"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    column_id: Mapped[int] = mapped_column(ForeignKey("columns.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)  # 1-high, 5-low
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    column: Mapped[Optional["BoardColumn"]] = relationship("BoardColumn", back_populates="tasks")
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary="task_tags", back_populates="tasks"
    )
    assignees: Mapped[List["Assignment"]] = relationship(
        "Assignment", back_populates="task", cascade="all,delete-orphan"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="task", cascade="all,delete-orphan"
    )

    __table_args__ = (
        Index("ix_task_project", "project_id"),
        Index("ix_task_column", "column_id"),
        Index("ix_task_due_date", "due_date"),
        Index("ix_task_priority", "priority"),
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # e.g., #RRGGBB

    project: Mapped["Project"] = relationship("Project", back_populates="tags")
    tasks: Mapped[List["Task"]] = relationship(
        "Task", secondary="task_tags", back_populates="tags"
    )

    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_tag_project_name"),
        Index("ix_tag_project", "project_id"),
    )


class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        Index("ix_tasktag_task", "task_id"),
        Index("ix_tasktag_tag", "tag_id"),
        UniqueConstraint("task_id", "tag_id", name="uq_task_tag"),
    )


class Assignment(Base):
    __tablename__ = "assignments"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="assignments")
    task: Mapped["Task"] = relationship("Task", back_populates="assignees")

    __table_args__ = (
        Index("ix_assignment_user", "user_id"),
        Index("ix_assignment_task", "task_id"),
    )


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    metadata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    task: Mapped["Task"] = relationship("Task", back_populates="activities")
    actor: Mapped["User"] = relationship("User", back_populates="activities")

    __table_args__ = (
        Index("ix_activity_task", "task_id"),
        Index("ix_activity_actor", "actor_id"),
        Index("ix_activity_created_at", "created_at"),
    )
