from fastapi import APIRouter, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.user import service
from bounded_contexts.user.models import User, UserPermissions
from bounded_contexts.user.schemas import (
    UserCreate,
    LoginResponse,
    UserResponse,
    UserUpdate,
)
from core.exceptions import AdminRequired
from core.services.auth import create_access_token, validate_user_token
from infra.database import get_session


router = APIRouter(prefix="/users", tags=["User"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> LoginResponse:
    user = service.authenticate_user(form_data.username, form_data.password, session)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "team_id": str(user.team_id),
        }
    )

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", status_code=200)
async def get_current_user(
    current_user: User = Depends(validate_user_token),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post("/", status_code=201)
async def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> User:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    return service.create_user(user_data, current_user, session)


@router.get("/team-users", status_code=200)
async def get_team_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[UserResponse]:
    users = service.get_users_by_team(current_user, session)
    users.insert(0, current_user)

    return [UserResponse.model_validate(user) for user in users]


@router.get("/name/{name_snippet}", status_code=200)
async def get_users_by_name_and_permission_type(
    name_snippet: str,
    permission_type: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[UserResponse]:
    if permission_type:
        permission_type = UserPermissions(permission_type)
    users = service.get_users_by_name_in_and_permission_type(
        name_snippet, permission_type, current_user.team_id, session
    )

    return [UserResponse.model_validate(user) for user in users]


@router.get("/email/{email_snippet}", status_code=200)
async def get_users_by_email_and_permission_type(
    email_snippet: str,
    permission_type: str | None = Query(default=None),
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[UserResponse]:
    if permission_type:
        permission_type = UserPermissions(permission_type)
    users = service.get_users_by_email_in_and_permission_type(
        email_snippet, permission_type, current_user.team_id, session
    )

    return [UserResponse.model_validate(user) for user in users]


@router.get("/type/{permission_type}", status_code=200)
async def get_users_by_permission_type(
    permission_type: UserPermissions,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[UserResponse]:
    users = service.get_users_by_permission_type(
        permission_type, current_user.team_id, session
    )

    return [UserResponse.model_validate(user) for user in users]


@router.get("/{user_id}", status_code=200)
async def get_user(user_id: UUID, session: Session = Depends(get_session)) -> User:
    return service.get_user_by_id(user_id, session)


@router.patch("/{user_id}", status_code=200)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> UserResponse:
    user_updated = service.update_user(user_id, user_data, session, current_user)

    return UserResponse.model_validate(user_updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.delete_user(user_id, current_user, session)
