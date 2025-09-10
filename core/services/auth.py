from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session

from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserReadRepo
from core.settings import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_ALGORITHM, JWT_KEY
from infra.database import get_session

security = HTTPBearer()


@dataclass
class _InvalidAccessToken(HTTPException):
    status_code = 401
    detail = "Sessão expirada ou inválida. Por favor, faça login novamente."
    headers = {"WWW-Authenticate": "Bearer"}


@dataclass
class _InvalidToken(HTTPException):
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


def general_validade_token(token: str):
    try:
        payload = jwt.decode(token, JWT_KEY, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except JWTError:
        raise _InvalidToken()
