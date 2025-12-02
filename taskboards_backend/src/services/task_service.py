from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.db.models import Assignment, Task, TaskTag


class TaskFilters:
    def __init__(
        self,
        project_id: Optional[int] = None,
        tag_ids: Optional[Sequence[int]] = None,
        assignee_id: Optional[int] = None,
        priority: Optional[int] = None,
        due_from: Optional[datetime] = None,
        due_to: Optional[datetime] = None,
        search: Optional[str] = None,
        status_column_id: Optional[int] = None,
    ) -> None:
        self.project_id = project_id
        self.tag_ids = list(tag_ids) if tag_ids else None
        self.assignee_id = assignee_id
        self.priority = priority
        self.due_from = due_from
        self.due_to = due_to
        self.search = search
        self.status_column_id = status_column_id


# PUBLIC_INTERFACE
def filter_tasks(db: Session, filters: TaskFilters) -> List[Task]:
    """
    Filter tasks using flexible criteria.

    Supported filters: project_id, tag_ids, assignee_id, priority, due_from, due_to, search, status_column_id
    """
    q = db.query(Task).distinct()
    if filters.project_id is not None:
        q = q.filter(Task.project_id == filters.project_id)
    if filters.status_column_id is not None:
        q = q.filter(Task.column_id == filters.status_column_id)
    if filters.priority is not None:
        q = q.filter(Task.priority == filters.priority)
    if filters.due_from is not None:
        q = q.filter(Task.due_date >= filters.due_from)
    if filters.due_to is not None:
        q = q.filter(Task.due_date <= filters.due_to)
    if filters.search:
        s = f"%{filters.search.lower()}%"
        q = q.filter(or_(func.lower(Task.title).like(s), func.lower(Task.description).like(s)))
    if filters.tag_ids:
        q = q.join(TaskTag, TaskTag.task_id == Task.id).filter(TaskTag.tag_id.in_(filters.tag_ids))
    if filters.assignee_id is not None:
        q = q.join(Assignment, Assignment.task_id == Task.id).filter(Assignment.user_id == filters.assignee_id)

    q = q.order_by(Task.created_at.desc())
    return q.all()
