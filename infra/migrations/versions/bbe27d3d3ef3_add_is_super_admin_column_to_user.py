"""add is_super_admin column to user

Revision ID: bbe27d3d3ef3
Revises: f721d715965e
Create Date: 2025-05-22 11:36:43.857888

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bbe27d3d3ef3"
down_revision: Union[str, None] = "f721d715965e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "is_super_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
