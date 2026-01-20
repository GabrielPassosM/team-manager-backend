"""create ix_user_team_id

Revision ID: 8be19d95af73
Revises: bbe27d3d3ef3
Create Date: 2025-05-26 10:13:10.597437

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "8be19d95af73"
down_revision: Union[str, None] = "bbe27d3d3ef3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_user_deleted", table_name="user")

    op.create_index(op.f("ix_user_team_id_deleted"), "user", ["team_id", "deleted"])


def downgrade() -> None:
    """Downgrade schema."""
    pass
