"""add player_id to user

Revision ID: 8455e9132847
Revises: 0990b847827e
Create Date: 2025-06-09 15:35:42.853145

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8455e9132847"
down_revision: Union[str, None] = "0990b847827e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("player_id", sa.Uuid(), nullable=True))

    op.create_foreign_key(
        "fk_user_player_id",
        source_table="user",
        referent_table="player",
        local_cols=["player_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )

    op.create_unique_constraint("uq_user_player_id", "user", ["player_id"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
