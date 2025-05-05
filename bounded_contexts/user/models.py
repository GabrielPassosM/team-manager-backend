from uuid import UUID

from sqlmodel import Field

from core.models.base import BaseTable


class User(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id")
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=254, unique=True, index=True)
    hashed_password: str = Field(max_length=60)
    is_admin: bool = Field(default=False)
