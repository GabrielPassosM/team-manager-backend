from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.team import service
from bounded_contexts.team.models import Team
from bounded_contexts.team.schemas import TeamCreate
from bounded_contexts.user.models import User
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/teams", tags=["Team"])


@router.post("/", status_code=201)
async def create_team(
    team_data: TeamCreate,
    session: Session = Depends(get_session),
) -> Team:
    return service.create_team(team_data, session)


@router.get("/{team_id}", status_code=200)
async def get_team(
    team_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> Team:
    return service.get_team_by_id(team_id, session)


@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: UUID, session: Session = Depends(get_session)) -> None:
    return service.delete_team(team_id, session)
