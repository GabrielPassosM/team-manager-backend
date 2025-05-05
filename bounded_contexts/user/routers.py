from fastapi import APIRouter
from uuid import UUID

from bounded_contexts.user import service
from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserCreate

router = APIRouter(prefix="/users", tags=["User"])


@router.post("/", status_code=201)
async def create_user(
    user_data: UserCreate,
) -> User:
    return service.create_user(user_data)


@router.get("/{user_id}", status_code=200)
async def get_user(user_id: UUID) -> User:
    return service.get_user_by_id(user_id)


@router.get("/team/{team_id}", status_code=200)
async def get_users_by_team(team_id: UUID) -> list[User]:
    return service.get_users_by_team(team_id)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: UUID) -> None:
    return service.delete_user(user_id)
