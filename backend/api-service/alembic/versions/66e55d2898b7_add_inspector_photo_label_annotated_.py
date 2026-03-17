"""add_inspector_photo_label_annotated_updated_at_edit_history

Revision ID: 66e55d2898b7
Revises: 8f7157c0a392
Create Date: 2026-03-17 02:13:49.529651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66e55d2898b7'
down_revision: Union[str, Sequence[str], None] = '8f7157c0a392'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('issue_edit_history',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('issue_id', sa.String(), nullable=False),
    sa.Column('field_changed', sa.String(), nullable=False),
    sa.Column('old_value', sa.String(), nullable=True),
    sa.Column('new_value', sa.String(), nullable=True),
    sa.Column('changed_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['issue_id'], ['inspection_issues.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('garment_photos', sa.Column('photo_label', sa.String(), nullable=True))
    op.add_column('garment_photos', sa.Column('annotated_file_path', sa.String(), nullable=True))
    op.add_column('inspection_issues', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('inspection_records', sa.Column('inspector_id', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('inspection_records', 'inspector_id')
    op.drop_column('inspection_issues', 'updated_at')
    op.drop_column('garment_photos', 'annotated_file_path')
    op.drop_column('garment_photos', 'photo_label')
    op.drop_table('issue_edit_history')
