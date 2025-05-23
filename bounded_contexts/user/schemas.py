from uuid import UUID

from pydantic import BaseModel, field_validator

from bounded_contexts.user.exceptions import PasswordToLong
from core.schemas import BaseSchema


class UserCreate(BaseModel):
    team_id: UUID
    name: str
    email: str
    password: str
    is_admin: bool = False

    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) > 72:
            raise PasswordToLong()

        return value


class _UserBasicResponse(BaseSchema):
    id: UUID
    name: str
    email: str
    team_id: UUID
    is_admin: bool
    is_super_admin: bool


class UserLoginResponse(_UserBasicResponse):
    pass


class LoginResponse(BaseModel):
    access_token: str
    user: UserLoginResponse


class CurrentUserResponse(_UserBasicResponse):
    pass
