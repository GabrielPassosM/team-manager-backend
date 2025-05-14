"""add three team columns

Revision ID: 4481aca197e1
Revises: 9d890a45be68
Create Date: 2025-05-13 20:43:05.361837

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4481aca197e1"
down_revision: Union[str, None] = "9d890a45be68"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("team", sa.Column("season_start_date", sa.Date(), nullable=True))
    op.add_column("team", sa.Column("season_end_date", sa.Date(), nullable=True))
    op.add_column(
        "team", sa.Column("primary_color", sa.String(length=10), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
