"""add max players or users to team

Revision ID: 08f0ab1182c9
Revises: 5b74c414ae7d
Create Date: 2025-09-15 14:26:07.833641

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "08f0ab1182c9"
down_revision: Union[str, None] = "5b74c414ae7d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "team",
        sa.Column(
            "max_players_or_users", sa.Integer(), nullable=False, server_default="30"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
