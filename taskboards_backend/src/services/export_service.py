import csv
import io
from typing import Iterable

from src.db.models import Task


# PUBLIC_INTERFACE
def tasks_to_csv(tasks: Iterable[Task]) -> bytes:
    """
    Convert a list of Task ORM objects to CSV bytes.

    Columns: id, project_id, column_id, title, description, priority, due_date, created_at, updated_at, tag_names
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["id", "project_id", "column_id", "title", "description", "priority", "due_date", "created_at", "updated_at", "tag_names"]
    )
    for t in tasks:
        tag_names = ",".join(sorted(set([tag.name for tag in (t.tags or [])])))
        writer.writerow(
            [
                t.id,
                t.project_id,
                t.column_id if t.column_id is not None else "",
                t.title,
                (t.description or "").replace("\n", " ").replace("\r", " "),
                t.priority,
                t.due_date.isoformat() if t.due_date else "",
                t.created_at.isoformat() if t.created_at else "",
                t.updated_at.isoformat() if t.updated_at else "",
                tag_names,
            ]
        )
    return output.getvalue().encode("utf-8")
