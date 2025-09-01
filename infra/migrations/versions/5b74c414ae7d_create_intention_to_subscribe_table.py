"""create intention_to_subscribe table

Revision ID: 5b74c414ae7d
Revises: 5cf9b8205504
Create Date: 2025-08-23 19:38:59.508748

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5b74c414ae7d"
down_revision: Union[str, None] = "5cf9b8205504"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow

    op.create_table(
        "intention_to_subscribe",
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
        # specific to intention_to_subscribe
        sa.Column("user_name", sa.String(length=255), nullable=False),
        sa.Column("user_email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("team_name", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("user_email", name="uq_intention_user_email"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
