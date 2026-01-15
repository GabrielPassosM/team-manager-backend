"""terms of use

Revision ID: e060d8081639
Revises: 2aa9832abd1f
Create Date: 2026-01-12 14:41:12.141746

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e060d8081639"
down_revision: Union[str, None] = "2aa9832abd1f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "terms_of_use",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_terms_of_use_version",
        "terms_of_use",
        ["version"],
        unique=True,
    )

    op.create_index(
        "ix_terms_of_use_is_active",
        "terms_of_use",
        ["is_active"],
    )

    op.create_table(
        "user_terms_acceptance",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("terms_version", sa.Integer(), nullable=False),
        sa.Column("accepted_at", sa.DateTime(), nullable=False),
    )

    op.create_index(
        "ix_user_terms_acceptance_terms_version",
        "user_terms_acceptance",
        ["terms_version"],
    )

    op.add_column(
        "user",
        sa.Column(
            "terms_accepted_version",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_user_terms_accepted_version",
        "user",
        ["terms_accepted_version"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
