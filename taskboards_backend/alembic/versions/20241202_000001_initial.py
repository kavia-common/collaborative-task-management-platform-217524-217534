"""initial

Revision ID: 20241202_000001
Revises:
Create Date: 2025-12-02 00:00:01.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241202_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # projects
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_project_owner", "projects", ["owner_id"])
    op.create_unique_constraint("uq_project_owner_name", "projects", ["owner_id", "name"])

    # columns
    op.create_table(
        "columns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_column_project", "columns", ["project_id"])
    op.create_unique_constraint("uq_column_project_name", "columns", ["project_id", "name"])

    # tasks
    op.create_table(
        "tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("column_id", sa.Integer(), sa.ForeignKey("columns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("due_date", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_task_project", "tasks", ["project_id"])
    op.create_index("ix_task_column", "tasks", ["column_id"])
    op.create_index("ix_task_due_date", "tasks", ["due_date"])
    op.create_index("ix_task_priority", "tasks", ["priority"])

    # tags
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
    )
    op.create_index("ix_tag_project", "tags", ["project_id"])
    op.create_unique_constraint("uq_tag_project_name", "tags", ["project_id", "name"])

    # task_tags
    op.create_table(
        "task_tags",
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_tasktag_task", "task_tags", ["task_id"])
    op.create_index("ix_tasktag_tag", "task_tags", ["tag_id"])
    op.create_unique_constraint("uq_task_tag", "task_tags", ["task_id", "tag_id"])

    # assignments
    op.create_table(
        "assignments",
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("assigned_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_assignment_user", "assignments", ["user_id"])
    op.create_index("ix_assignment_task", "assignments", ["task_id"])

    # activities
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), sa.ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_activity_task", "activities", ["task_id"])
    op.create_index("ix_activity_actor", "activities", ["actor_id"])
    op.create_index("ix_activity_created_at", "activities", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_activity_created_at", table_name="activities")
    op.drop_index("ix_activity_actor", table_name="activities")
    op.drop_index("ix_activity_task", table_name="activities")
    op.drop_table("activities")

    op.drop_index("ix_assignment_task", table_name="assignments")
    op.drop_index("ix_assignment_user", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("ix_tasktag_tag", table_name="task_tags")
    op.drop_index("ix_tasktag_task", table_name="task_tags")
    op.drop_constraint("uq_task_tag", "task_tags", type_="unique")
    op.drop_table("task_tags")

    op.drop_constraint("uq_tag_project_name", "tags", type_="unique")
    op.drop_index("ix_tag_project", table_name="tags")
    op.drop_table("tags")

    op.drop_index("ix_task_priority", table_name="tasks")
    op.drop_index("ix_task_due_date", table_name="tasks")
    op.drop_index("ix_task_column", table_name="tasks")
    op.drop_index("ix_task_project", table_name="tasks")
    op.drop_table("tasks")

    op.drop_constraint("uq_column_project_name", "columns", type_="unique")
    op.drop_index("ix_column_project", table_name="columns")
    op.drop_table("columns")

    op.drop_constraint("uq_project_owner_name", "projects", type_="unique")
    op.drop_index("ix_project_owner", table_name="projects")
    op.drop_table("projects")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
