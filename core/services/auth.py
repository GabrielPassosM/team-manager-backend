from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from uuid import UUID

from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session
from starlette.responses import JSONResponse

from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from core.settings import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_KEY,
    REFRESH_TOKEN_SECURE_BOOL,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ENV_CONFIG,
)
from infra.database import get_session

security = HTTPBearer()


@dataclass
class _InvalidAccessToken(HTTPException):
    status_code = 401
    detail = "Sessão expirada ou inválida. Por favor, faça login novamente."
    headers = {"WWW-Authenticate": "Bearer"}


@dataclass
class InvalidToken(HTTPException):
    status_code = 400
    detail = "Token inválido ou expirado."


def create_jwt_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_KEY, algorithm=JWT_ALGORITHM)


def validate_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        team_id: str = payload.get("team_id")
        if not user_id or not team_id:
            raise _InvalidAccessToken()
    except JWTError:
        raise _InvalidAccessToken()

    user = UserReadRepo(session=session).get_by_id(user_id)
    if not user or str(user.team_id) != team_id:
        raise _InvalidAccessToken()

    return user


def general_validade_token(
    token: str, ignore_exp: bool = False, raise_custom_error: bool = True
) -> str:
    options = {"verify_exp": False} if ignore_exp else {}
    try:
        payload = jwt.decode(
            token, JWT_KEY, algorithms=[JWT_ALGORITHM], options=options
        )
        return payload["sub"]
    except Exception:
        if raise_custom_error:
            raise InvalidToken()
        raise


def create_refresh_token(
    response: JSONResponse, user_id: UUID, is_demo_user: bool, session: Session
) -> JSONResponse:
    from bounded_contexts.user.service import create_logged_user

    refresh_token = create_logged_user(user_id, is_demo_user, session)

    if ENV_CONFIG == "production":
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=REFRESH_TOKEN_SECURE_BOOL,
            samesite="none",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
            domain=".forquilha.app.br",
        )
    else:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        )

    return response
