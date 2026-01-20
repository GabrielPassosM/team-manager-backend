from fastapi import APIRouter, Depends, Query, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.user import service
from bounded_contexts.user.models import User, UserPermissions
from bounded_contexts.user.schemas import (
    UserCreate,
    UserResponse,
    UserUpdate,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    FirstAccessStart,
    FirstAccessConfirmation,
)
from core.exceptions import AdminRequired, SuperAdminRequired
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/login", status_code=200)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> JSONResponse:
    return service.login(form_data.username, form_data.password, session)


@router.post("/logout", status_code=200)
def logout(
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_session),
) -> JSONResponse:
    return service.logout(refresh_token, session)


@router.post("/forgot-password", status_code=200)
def forgot_password(
    data: ForgotPasswordRequest,
    session: Session = Depends(get_session),
) -> str:
    return service.send_reset_password_email(data.email, session)


@router.post("/first-access-start", status_code=200)
def first_access_start(
    data: FirstAccessStart,
    session: Session = Depends(get_session),
) -> str:
    return service.make_user_first_access(data, session)


@router.post("/first-access-confirmation", status_code=200)
def first_access_confirmation(
    data: FirstAccessConfirmation,
    session: Session = Depends(get_session),
) -> None:
    return service.confirm_user_first_access(data, session)


@router.post("/reset-password", status_code=200)
def reset_password(
    data: ResetPasswordRequest,
    session: Session = Depends(get_session),
) -> None:
    service.reset_password(data, session)


@router.post("/refresh", status_code=200)
def refresh_access_token(
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """
    Refreshes the access token using the provided refresh token.

    Always return 200 even if the refresh token is invalid or expired.
    """
    return service.refresh_access_token(refresh_token, session)


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
) -> UserResponse:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    created_user = service.create_user(user_data, current_user, session)
    return UserResponse.model_validate(created_user)


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
    update_data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> UserResponse:
    user_updated = service.update_user(user_id, update_data, session, current_user)

    return UserResponse.model_validate(user_updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.delete_user(user_id, current_user, session)


@router.delete("/clear/logged-users", status_code=200)
async def clear_expired_logged_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> int:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    return service.clear_expired_logged_users(session)
