"""create championship table

Revision ID: ac06307cc7e8
Revises: 8be19d95af73
Create Date: 2025-05-26 10:17:04.401059

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ac06307cc7e8"
down_revision: Union[str, None] = "8be19d95af73"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow

    op.create_table(
        "championship",
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
        # specific to championship
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_league_format",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("final_stage", sa.String(length=100), nullable=True, default=None),
        sa.Column("final_position", sa.Integer(), nullable=True, default=None),
    )

    op.create_index(
        "ix_championship_team_id_deleted", "championship", ["team_id", "deleted"]
    )
    op.create_index(
        op.f("ix_championship_is_league_format"), "championship", ["is_league_format"]
    )

    sa.UniqueConstraint("team_id", "name", name="uq_championship_team_id_name")


def downgrade() -> None:
    """Downgrade schema."""
    pass
