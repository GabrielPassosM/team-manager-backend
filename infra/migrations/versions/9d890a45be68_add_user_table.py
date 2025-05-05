"""add user table

Revision ID: 9d890a45be68
Revises: 0dabf07d3b12
Create Date: 2025-05-04 13:55:10.375312

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from libs.datetime import utcnow

# revision identifiers, used by Alembic.
revision: str = "9d890a45be68"
down_revision: Union[str, None] = "0dabf07d3b12"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, default=utcnow
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, default=utcnow
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        # specific to user
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("hashed_password", sa.String(length=60), nullable=False),
        sa.Column(
            "is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.UniqueConstraint("team_id", "email", name="uq_user_email"),
    )
    op.create_index("ix_user_deleted", "user", ["deleted"])
    op.create_index("ix_user_email", "user", ["email"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
