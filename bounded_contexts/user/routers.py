from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.user import service
from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserCreate, LoginResponse, UserLoginResponse
from core.services.auth import create_access_token
from infra.database import get_session


router = APIRouter(prefix="/users", tags=["User"])


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> LoginResponse:
    user = service.authenticate_user(form_data.username, form_data.password, session)
    access_token = create_access_token(data={"sub": user.email})

    return LoginResponse(
        access_token=access_token,
        user=UserLoginResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            team_id=user.team_id,
            is_admin=user.is_admin,
        ),
    )


@router.post("/", status_code=201)
async def create_user(
    user_data: UserCreate,
    session: Session = Depends(get_session),
) -> User:
    return service.create_user(user_data, session)


@router.get("/{user_id}", status_code=200)
async def get_user(user_id: UUID, session: Session = Depends(get_session)) -> User:
    return service.get_user_by_id(user_id, session)


@router.get("/team/{team_id}", status_code=200)
async def get_users_by_team(
    team_id: UUID, session: Session = Depends(get_session)
) -> list[User]:
    return service.get_users_by_team(team_id, session)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID, session: Session = Depends(get_session)) -> None:
    return service.delete_user(user_id, session)
