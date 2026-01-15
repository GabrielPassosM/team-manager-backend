from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel

from libs.datetime import utcnow


class TermsOfUse(SQLModel, table=True):
    __tablename__ = "terms_of_use"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    version: int = Field(index=True, nullable=False, unique=True)
    content: str = Field(nullable=False)
    is_active: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utcnow)


class UserTermsAcceptance(SQLModel, table=True):
    __tablename__ = "user_terms_acceptance"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
    )
    user_id: UUID = Field(
        foreign_key="user.id",
        index=True,
        ondelete="CASCADE",
    )
    terms_version: int = Field(nullable=False, index=True)
    accepted_at: datetime = Field(default_factory=utcnow)
