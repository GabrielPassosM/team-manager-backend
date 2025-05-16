"""add default to primary_color

Revision ID: f721d715965e
Revises: 4481aca197e1
Create Date: 2025-05-16 19:39:26.698447

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f721d715965e"
down_revision: Union[str, None] = "4481aca197e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "team",
        "primary_color",
        existing_type=sa.String(length=10),
        server_default=sa.text("'#2563eb'"),
        existing_nullable=True,
    )

    op.execute("UPDATE team SET primary_color = '#2563eb' WHERE primary_color IS NULL")


def downgrade() -> None:
    """Downgrade schema."""
    pass
