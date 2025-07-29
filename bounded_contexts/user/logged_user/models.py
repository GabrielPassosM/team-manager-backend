from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

from libs.datetime import utcnow

if TYPE_CHECKING:
    from bounded_contexts.user.models import User


class LoggedUser(SQLModel, table=True):
    __tablename__ = "logged_user"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    user_id: UUID = Field(foreign_key="user.id")
    refresh_token: str = Field(unique=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=utcnow)

    user: "User" = Relationship(back_populates="logged_user")
