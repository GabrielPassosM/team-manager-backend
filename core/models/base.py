from datetime import datetime

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime

from libs.base_types.uuid import BaseUUID
from libs.datetime import utcnow


class BaseTable(SQLModel):
    id: BaseUUID = Field(
        default_factory=BaseUUID,
        primary_key=True,
    )
    deleted: bool = Field(default=False, index=True)

    created_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = Field(
        default_factory=utcnow, sa_column=Column(DateTime(timezone=True))
    )

    created_by: BaseUUID | None = Field(nullable=True, default=None)
    updated_by: BaseUUID | None = Field(nullable=True, default=None)
