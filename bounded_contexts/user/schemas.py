from uuid import UUID

from pydantic import BaseModel, field_validator

from bounded_contexts.user.exceptions import PasswordToLong
from core.schemas import BaseSchema


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    is_admin: bool = False
    is_super_admin: bool = False
    player_id: UUID | None = None

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) > 72:
            raise PasswordToLong()

        return value


class UserUpdate(BaseModel):
    name: str
    email: str
    password: str | None = None
    player_id: UUID | None = None


class UserPlayer(BaseSchema):
    id: UUID
    name: str
    shirt_number: int | None = None


class UserResponse(BaseSchema):
    id: UUID
    name: str
    email: str
    team_id: UUID
    is_admin: bool
    is_super_admin: bool
    player: UserPlayer | None = None


class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse
