"""add detected_photos_key to inspection_records

Revision ID: add_detected_photos_key
Revises: add_photo_index_2024
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_detected_photos_key"
down_revision = "add_photo_index_2024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "inspection_records",
        sa.Column("detected_photos_key", sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("inspection_records", "detected_photos_key")
