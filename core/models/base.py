from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field
from sqlalchemy import DateTime

from libs.datetime import utcnow


class BaseTable(SQLModel):
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    deleted: bool = Field(default=False, index=True)

    created_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )
    updated_at: datetime = Field(
        default_factory=utcnow, sa_type=DateTime(timezone=True)
    )

    created_by: UUID | None = Field(nullable=True, default=None)
    updated_by: UUID | None = Field(nullable=True, default=None)
