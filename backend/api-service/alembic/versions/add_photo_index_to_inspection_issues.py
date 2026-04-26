"""add photo_index to inspection_issues

Revision ID: add_photo_index_2024
Revises: 439ccd9639e5
Create Date: 2024-04-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_photo_index_2024"
down_revision = "439ccd9639e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add photo_index column to inspection_issues
    op.add_column(
        "inspection_issues",
        sa.Column("photo_index", sa.Integer(), nullable=True)
    )


def downgrade() -> None:
    # Remove photo_index column
    op.drop_column("inspection_issues", "photo_index")
