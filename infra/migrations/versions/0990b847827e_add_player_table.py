"""add player table

Revision ID: 0990b847827e
Revises: 963b86282604
Create Date: 2025-06-05 14:42:28.160496

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0990b847827e"
down_revision: Union[str, None] = "963b86282604"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow

    op.create_table(
        "player",
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
        # Specific to player
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image_url", sa.String(), nullable=True),
        sa.Column("shirt_number", sa.Integer(), nullable=True),
        sa.Column("position", sa.String(), nullable=False),
    )

    op.create_index(op.f("ix_player_team_id_deleted"), "player", ["team_id", "deleted"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
