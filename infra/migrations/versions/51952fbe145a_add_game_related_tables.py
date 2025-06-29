"""add game related tables

Revision ID: 51952fbe145a
Revises: 8455e9132847
Create Date: 2025-06-14 14:54:46.387962

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "51952fbe145a"
down_revision: Union[str, None] = "8455e9132847"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from libs.datetime import utcnow
    from core.consts import DEFAULT_ADVERSARY

    op.create_table(
        "game",
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
        # specific to game
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column(
            "championship_id",
            sa.Uuid(),
            sa.ForeignKey("championship.id"),
            nullable=False,
        ),
        sa.Column(
            "adversary",
            sa.String(length=255),
            nullable=False,
            server_default=DEFAULT_ADVERSARY,
        ),
        sa.Column("date_hour", sa.DateTime(timezone=True), nullable=False),
        sa.Column("round", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(length=100), nullable=True),  # StageOptions
        sa.Column(
            "is_home", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "is_wo", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column("team_score", sa.Integer(), nullable=True),
        sa.Column("adversary_score", sa.Integer(), nullable=True),
        sa.Column("team_penalty_score", sa.Integer(), nullable=True),
        sa.Column("adversary_penalty_score", sa.Integer(), nullable=True),
    )
    op.create_index("ix_game_team_id_deleted", "game", ["team_id", "deleted"])
    op.create_index(
        "ix_game_championship_id_deleted", "game", ["championship_id", "deleted"]
    )

    op.create_table(
        "game_player_availability",
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
        # specific to game_player_availability
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column("game_id", sa.Uuid(), sa.ForeignKey("game.id"), nullable=False),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("player.id"), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),  # AvailabilityStatus
        sa.UniqueConstraint("game_id", "player_id", name="uq_gpa_game_id_player_id"),
    )
    op.create_index(
        "ix_gpa_game_id",
        "game_player_availability",
        ["game_id"],
    )

    op.create_table(
        "game_player_stat",
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
        # specific to game_player_stat
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("team.id"), nullable=False),
        sa.Column("game_id", sa.Uuid(), sa.ForeignKey("game.id"), nullable=False),
        sa.Column("player_id", sa.Uuid(), sa.ForeignKey("player.id"), nullable=True),
        sa.Column(
            "related_stat_id",
            sa.Uuid(),
            sa.ForeignKey("game_player_stat.id"),
            nullable=True,
        ),
        sa.Column("stat", sa.String(length=50), nullable=False),  # StatOptions
        sa.Column("quantity", sa.Integer(), nullable=False),
        # sa.UniqueConstraint("game_id", "player_id", "stat", name="uq_gps_game_id_player_id_stat")
    )
    op.create_index(
        "ix_gps_game_id_deleted",
        "game_player_stat",
        ["game_id", "deleted"],
    )
    op.create_index(
        "ix_gps_player_id_stat",
        "game_player_stat",
        ["player_id", "stat"],
    )
    op.create_index(
        "ix_gps_team_id_stat_deleted",
        "game_player_stat",
        ["team_id", "stat", "deleted"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
