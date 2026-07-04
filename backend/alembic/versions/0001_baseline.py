"""baseline schema + seed settings

Revision ID: 0001
Revises:
Create Date: 2026-07-04

Baseline migration. upgrade() calls Base.metadata.create_all(), which is
safe here because this is the very first revision against an empty
database - there's no existing schema for create_all() to silently fail to
alter. Every future schema change gets its own real migration instead.
"""
from alembic import op
import sqlalchemy as sa

from app import models

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    models.Base.metadata.create_all(bind=bind)

    settings_table = sa.table(
        "sfc_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Float),
        sa.column("description", sa.String),
    )
    op.bulk_insert(settings_table, [
        {"key": "labour_rate", "value": 350.0, "description": "Standard burdened labour rate per hour (ZAR), from the Master Price List."},
        {"key": "kerf_mm", "value": 3.5, "description": "Saw blade kerf allowance used in cutting-list yield calculations."},
        {"key": "wastage_factor", "value": 1.10, "description": "Board/linear-stock wastage multiplier (10%) applied across all five typologies."},
    ])


def downgrade() -> None:
    pass
