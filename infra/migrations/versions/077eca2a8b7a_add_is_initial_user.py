"""add is_initial_user

Revision ID: 077eca2a8b7a
Revises: d37bc6a611a0
Create Date: 2026-01-12 08:31:08.634873

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "077eca2a8b7a"
down_revision: Union[str, None] = "d37bc6a611a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "is_initial_user",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
