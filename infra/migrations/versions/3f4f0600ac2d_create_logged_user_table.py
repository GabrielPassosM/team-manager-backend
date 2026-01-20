"""create logged_user table

Revision ID: 3f4f0600ac2d
Revises: 0f84672b5ef0
Create Date: 2025-07-23 08:15:25.522497

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3f4f0600ac2d"
down_revision: Union[str, None] = "0f84672b5ef0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow

    op.create_table(
        "logged_user",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, default=utcnow
        ),
        sa.UniqueConstraint("refresh_token", name="uq_logged_user_refresh_token"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
