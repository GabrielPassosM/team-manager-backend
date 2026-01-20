"""rename max_players column

Revision ID: 2aa9832abd1f
Revises: 077eca2a8b7a
Create Date: 2026-01-12 10:42:30.455450

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2aa9832abd1f"
down_revision: Union[str, None] = "077eca2a8b7a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "team",
        column_name="max_players_or_users",
        new_column_name="max_players",
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
