from enum import Enum
from uuid import UUID

from sqlmodel import Field

from core.models.base import BaseTable


class User(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id")
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=254, unique=True, index=True)
    hashed_password: str = Field(max_length=60)
    is_admin: bool = Field(default=False)
    is_super_admin: bool = Field(default=False)

    @property
    def has_admin_privileges(self) -> bool:
        return self.is_admin or self.is_super_admin


class UserPermissions(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

    @property
    def has_admin_privileges(self) -> bool:
        return self in (self.ADMIN, self.SUPER_ADMIN)
