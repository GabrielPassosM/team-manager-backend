"""recreate logged_user

Revision ID: 388fb1049af9
Revises: 3f4f0600ac2d
Create Date: 2025-07-30 16:57:59.269612

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "388fb1049af9"
down_revision: Union[str, None] = "3f4f0600ac2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow

    op.drop_table("logged_user")

    op.create_table(
        "logged_user",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
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
