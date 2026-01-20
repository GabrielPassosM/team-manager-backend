"""add code to team

Revision ID: d37bc6a611a0
Revises: 1bfb2b69c9c9
Create Date: 2025-10-03 12:05:22.547489

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "d37bc6a611a0"
down_revision: Union[str, None] = "1bfb2b69c9c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("team", sa.Column("code", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_team_code", "team", ["code"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
