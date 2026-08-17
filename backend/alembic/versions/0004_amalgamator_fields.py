"""add client_name, location, status to projects (Amalgamator support)

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-17

Adds the fields the cross-company Amalgamator status report needs:
client_name (structured, alongside the existing free-text client_info),
location (didn't exist at all before), and status (this app had no
project-lifecycle concept before now - projects were just costing
worksheets). Guards on existing columns first, same idempotent pattern
used in Engineering-Management-App's and QA Management's Amalgamator
migrations, so this stays safely re-runnable.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    existing_columns = {col["name"] for col in sa.inspect(bind).get_columns("sfc_projects")}

    if "client_name" not in existing_columns:
        op.add_column("sfc_projects", sa.Column("client_name", sa.String(length=255), nullable=True))
    if "location" not in existing_columns:
        op.add_column("sfc_projects", sa.Column("location", sa.String(length=300), nullable=True))
    if "status" not in existing_columns:
        op.add_column(
            "sfc_projects",
            sa.Column("status", sa.String(length=50), nullable=False, server_default="active"),
        )


def downgrade() -> None:
    op.drop_column("sfc_projects", "status")
    op.drop_column("sfc_projects", "location")
    op.drop_column("sfc_projects", "client_name")
