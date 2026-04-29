"""add user security fields: is_active, lockout, last_login, must_change_password

Revision ID: add_user_security_fields
Revises: add_detected_photos_key
Create Date: 2026-04-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "add_user_security_fields"
down_revision = "add_detected_photos_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("app_users", sa.Column("is_active", sa.Boolean(), nullable=True, server_default="1"))
    op.add_column("app_users", sa.Column("must_change_password", sa.Boolean(), nullable=True, server_default="0"))
    op.add_column("app_users", sa.Column("failed_login_count", sa.Integer(), nullable=True, server_default="0"))
    op.add_column("app_users", sa.Column("locked_until", sa.DateTime(), nullable=True))
    op.add_column("app_users", sa.Column("last_login_at", sa.DateTime(), nullable=True))
    op.add_column("app_users", sa.Column("updated_at", sa.DateTime(), nullable=True))

    # Mark existing default accounts as must_change_password
    op.execute(
        "UPDATE app_users SET must_change_password = TRUE WHERE username IN ('admin', 'staff')"
    )


def downgrade() -> None:
    op.drop_column("app_users", "updated_at")
    op.drop_column("app_users", "last_login_at")
    op.drop_column("app_users", "locked_until")
    op.drop_column("app_users", "failed_login_count")
    op.drop_column("app_users", "must_change_password")
    op.drop_column("app_users", "is_active")
