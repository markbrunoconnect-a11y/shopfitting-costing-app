"""add consumables_pct setting

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-04

Adds a flat consumables markup (screws, glue, sealant, tape, sandpaper -
small items not individually priced anywhere in the typology engines),
applied as a percentage of each component's material cost. Default 5%,
a rough industry-common figure for a blanket allowance - editable via the
Materials/Settings screen and intended to be recalibrated against real
jobs, same as labour_rate and wastage_factor.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    settings_table = sa.table(
        "sfc_settings",
        sa.column("key", sa.String),
        sa.column("value", sa.Float),
        sa.column("description", sa.String),
    )
    op.bulk_insert(settings_table, [
        {"key": "consumables_pct", "value": 5.0, "description": "Flat consumables markup (screws, glue, sealant, tape, etc.) as a % of material cost - not itemized, recalibrate against real jobs."},
    ])


def downgrade() -> None:
    op.execute("DELETE FROM sfc_settings WHERE key = 'consumables_pct'")
