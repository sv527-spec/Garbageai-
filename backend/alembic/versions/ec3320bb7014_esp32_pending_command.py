"""add esp32 pending command columns (cloud polling mode)

Revision ID: ec3320bb7014
Revises: 9488f3c7bd35
Create Date: 2026-08-07
"""
import sqlalchemy as sa
from alembic import op

revision = "ec3320bb7014"
down_revision = "9488f3c7bd35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("esp32_devices", sa.Column("pending_category", sa.String(), nullable=True))
    op.add_column("esp32_devices", sa.Column("pending_scan_id", sa.String(), nullable=True))
    op.add_column("esp32_devices", sa.Column("pending_created_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("esp32_devices", "pending_created_at")
    op.drop_column("esp32_devices", "pending_scan_id")
    op.drop_column("esp32_devices", "pending_category")
