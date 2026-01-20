"""add champ teamid name deleted uq

Revision ID: 963b86282604
Revises: ac06307cc7e8
Create Date: 2025-05-31 11:59:00.248163

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "963b86282604"
down_revision: Union[str, None] = "ac06307cc7e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE UNIQUE INDEX uq_championship_team_id_name_active
        ON championship (team_id, name)
        WHERE NOT deleted
    """)


def downgrade() -> None:
    """Downgrade schema."""
    pass
