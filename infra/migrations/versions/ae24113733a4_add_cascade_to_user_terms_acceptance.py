"""add cascade to user_terms_acceptance

Revision ID: ae24113733a4
Revises: e060d8081639
Create Date: 2026-01-16 13:08:04.146255

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ae24113733a4"
down_revision: Union[str, None] = "e060d8081639"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "user_terms_acceptance_user_id_fkey",
        "user_terms_acceptance",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "user_terms_acceptance_user_id_fkey",
        source_table="user_terms_acceptance",
        referent_table="user",
        local_cols=["user_id"],
        remote_cols=["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
