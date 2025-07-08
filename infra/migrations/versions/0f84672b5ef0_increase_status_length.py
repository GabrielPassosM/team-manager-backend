"""increase status length

Revision ID: 0f84672b5ef0
Revises: 51952fbe145a
Create Date: 2025-07-07 17:03:06.067440

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0f84672b5ef0"
down_revision: Union[str, None] = "51952fbe145a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "game_player_availability",
        "status",
        type_=sa.String(length=50),
        existing_type=sa.String(length=10),
        existing_nullable=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
