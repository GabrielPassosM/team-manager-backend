from fastapi import APIRouter, Depends, Query, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from sqlmodel import Session
from uuid import UUID
from bson import ObjectId

from bounded_contexts.user import service
from bounded_contexts.user.models import User, UserPermissions
from bounded_contexts.user.schemas import (
    UserCreate,
    LoginResponse,
    UserResponse,
    UserUpdate,
)
from core.consts import DEMO_USER_EMAIL
from core.exceptions import AdminRequired, SuperAdminRequired
from core.services.auth import create_access_token, validate_user_token
from core.settings import REFRESH_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_SECURE_BOOL
from infra.database import get_session
from libs.datetime import utcnow

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/login", status_code=200)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> JSONResponse:
    user = service.authenticate_user(form_data.username, form_data.password, session)

    # We create a new user every time it is a demo login
    is_demo_user = form_data.username == DEMO_USER_EMAIL
    if is_demo_user:
        user = service.create_user(
            user_data=UserCreate(
                name="Usuário Demonstração",
                email=f"{ObjectId()}@demofc.com",
                password=str(ObjectId()),
                is_admin=True,
            ),
            current_user=user,
            session=session,
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "team_id": str(user.team_id),
        }
    )

    refresh_token = service.create_logged_user(user.id, is_demo_user, session)

    response_data = LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    ).model_dump()

    response_data["user"]["id"] = str(response_data["user"]["id"])
    response_data["user"]["team_id"] = str(response_data["user"]["team_id"])
    if response_data["user"].get("player"):
        response_data["user"]["player"]["id"] = str(
            response_data["user"]["player"]["id"]
        )

    response = JSONResponse(content=response_data)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=REFRESH_TOKEN_SECURE_BOOL,
        samesite="none",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
    )

    return response


@router.post("/logout", status_code=200)
def logout(
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_session),
) -> JSONResponse:
    if not refresh_token:
        return JSONResponse(
            content={"detail": "refresh_token nao enviado"}, status_code=400
        )

    service.delete_logged_user(refresh_token, session)
    response = JSONResponse(
        content={"detail": "Logout realizado com sucesso"}, status_code=200
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=REFRESH_TOKEN_SECURE_BOOL,
        samesite="none",
    )
    return response


@router.post("/refresh", status_code=200)
def refresh_access_token(
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_session),
) -> JSONResponse:
    """
    Refreshes the access token using the provided refresh token.

    Always return 200 even if the refresh token is invalid or expired.
    """

    if not refresh_token:
        return JSONResponse(content={"error": "refresh_token inválido ou expirado"})

    logged_user = service.get_logged_user_by_token(refresh_token, session)

    response = JSONResponse(content={"error": "refresh_token inválido ou expirado"})
    if not logged_user:
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=REFRESH_TOKEN_SECURE_BOOL,
            samesite="none",
        )
        return response

    if not logged_user.expires_at.tzinfo:
        # SQLite test db does not support timezone-aware datetimes
        logged_user.expires_at = logged_user.expires_at.replace(tzinfo=utcnow().tzinfo)

    if logged_user.expires_at < utcnow():
        try:
            service.delete_logged_user(refresh_token, session)
        except Exception:
            # Ignore exception to at least delete the cookie.
            # We can remove expired users after.
            pass
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=REFRESH_TOKEN_SECURE_BOOL,
            samesite="none",
        )
        return response

    user = logged_user.user

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "team_id": str(user.team_id),
        }
    )

    return JSONResponse(content={"access_token": access_token})


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
