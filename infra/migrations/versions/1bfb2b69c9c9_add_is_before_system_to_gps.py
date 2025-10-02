"""add is_before_system to gps

Revision ID: 1bfb2b69c9c9
Revises: 08f0ab1182c9
Create Date: 2025-10-01 15:31:00.991251

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1bfb2b69c9c9"
down_revision: Union[str, None] = "08f0ab1182c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "game_player_stat",
        sa.Column(
            "is_before_system",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )

    op.add_column(
        "player",
        sa.Column(
            "has_before_system_stats",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
