from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlmodel import Field, Relationship

from core.models.base import BaseTable

if TYPE_CHECKING:
    from bounded_contexts.player.models import Player


class User(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id")
    player_id: UUID | None = Field(foreign_key="player.id", unique=True, nullable=True)
    name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=254, unique=True, index=True)
    hashed_password: str = Field(max_length=60)
    is_admin: bool = Field(default=False)
    is_super_admin: bool = Field(default=False)

    player: Optional["Player"] = Relationship(back_populates="user")
    logged_user: Optional["LoggedUser"] = Relationship(back_populates="user")

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


from bounded_contexts.user.logged_user.models import LoggedUser
