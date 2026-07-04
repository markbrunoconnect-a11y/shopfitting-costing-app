"""add fixture_category and labour_multiplier to items

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-04

Switches labour costing from estimated-hours x labour_rate to
material_cost x labour_multiplier, set per item based on a fixture
complexity category (Modular ~0.5-0.8x, Standard Joinery 1.0x,
Bespoke/Premium ~1.5-2.0x) - Mark's decision, replacing the placeholder
hours-based formulas since no real per-typology timing data exists yet.
labour_rate/labour_hours remain in the schema for reference but no longer
drive cost.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sfc_items", sa.Column("fixture_category", sa.String(length=50), nullable=True))
    op.add_column("sfc_items", sa.Column("labour_multiplier", sa.Float(), nullable=False, server_default="1.0"))


def downgrade() -> None:
    op.drop_column("sfc_items", "labour_multiplier")
    op.drop_column("sfc_items", "fixture_category")
