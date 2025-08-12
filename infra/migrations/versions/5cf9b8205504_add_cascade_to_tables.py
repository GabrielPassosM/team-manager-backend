"""add_cascade_to_tables

Revision ID: 5cf9b8205504
Revises: 388fb1049af9
Create Date: 2025-08-11 14:00:47.251018

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5cf9b8205504"
down_revision: Union[str, None] = "388fb1049af9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Player
    op.drop_constraint("player_team_id_fkey", "player", type_="foreignkey")
    op.create_foreign_key(
        "player_team_id_fkey",
        source_table="player",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # User
    op.drop_constraint("user_team_id_fkey", "user", type_="foreignkey")
    op.create_foreign_key(
        "user_team_id_fkey",
        source_table="user",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # Game
    op.drop_constraint("game_team_id_fkey", "game", type_="foreignkey")
    op.create_foreign_key(
        "game_team_id_fkey",
        source_table="game",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("game_championship_id_fkey", "game", type_="foreignkey")
    op.create_foreign_key(
        "game_championship_id_fkey",
        source_table="game",
        referent_table="championship",
        local_cols=["championship_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # Championship
    op.drop_constraint("championship_team_id_fkey", "championship", type_="foreignkey")
    op.create_foreign_key(
        "championship_team_id_fkey",
        source_table="championship",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # GamePlayerAvailability
    op.drop_constraint(
        "game_player_availability_team_id_fkey",
        "game_player_availability",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "game_player_availability_team_id_fkey",
        source_table="game_player_availability",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "game_player_availability_game_id_fkey",
        "game_player_availability",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "game_player_availability_game_id_fkey",
        source_table="game_player_availability",
        referent_table="game",
        local_cols=["game_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "game_player_availability_player_id_fkey",
        "game_player_availability",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "game_player_availability_player_id_fkey",
        source_table="game_player_availability",
        referent_table="player",
        local_cols=["player_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    # GamePlayerStat
    op.drop_constraint(
        "game_player_stat_team_id_fkey", "game_player_stat", type_="foreignkey"
    )
    op.create_foreign_key(
        "game_player_stat_team_id_fkey",
        source_table="game_player_stat",
        referent_table="team",
        local_cols=["team_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "game_player_stat_game_id_fkey", "game_player_stat", type_="foreignkey"
    )
    op.create_foreign_key(
        "game_player_stat_game_id_fkey",
        source_table="game_player_stat",
        referent_table="game",
        local_cols=["game_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint(
        "game_player_stat_player_id_fkey", "game_player_stat", type_="foreignkey"
    )
    op.create_foreign_key(
        "game_player_stat_player_id_fkey",
        source_table="game_player_stat",
        referent_table="player",
        local_cols=["player_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
