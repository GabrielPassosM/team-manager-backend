"""create team table

Revision ID: 0dabf07d3b12
Revises:
Create Date: 2025-04-30 10:49:00.398248

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from libs.datetime import utcnow

# revision identifiers, used by Alembic.
revision: str = "0dabf07d3b12"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "team",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column(
            "deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, default=utcnow
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, default=utcnow
        ),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("emblem_url", sa.String(), nullable=True),
        sa.Column("foundation_date", sa.Date(), nullable=True),
        sa.Column("paid_until", sa.Date(), nullable=False),
    )
    op.create_index("ix_team_deleted", "team", ["deleted"])


def downgrade() -> None:
    pass
