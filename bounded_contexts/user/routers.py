from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.user import service
from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserCreate
from infra.database import get_session

router = APIRouter(prefix="/users", tags=["User"])


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
