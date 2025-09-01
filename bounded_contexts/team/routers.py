from fastapi import APIRouter, Depends
from sqlmodel import Session
from uuid import UUID

from bounded_contexts.team import service
from bounded_contexts.team.models import Team
from bounded_contexts.team.schemas import (
    TeamCreate,
    CurrentTeamResponse,
    TeamUpdate,
    IntentionToSubscribeCreate,
)
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired, SuperAdminRequired
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/teams", tags=["Team"])


@router.post("/", status_code=201)
async def create_team(
    team_data: TeamCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> Team:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    return service.create_team(team_data, session)


@router.get("/me", status_code=200)
async def get_current_team(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> CurrentTeamResponse:
    team = service.get_team_by_id(current_user.team_id, session)

    return CurrentTeamResponse.model_validate(team)


@router.patch("/me", status_code=200)
async def update_current_team(
    team_data: TeamUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> CurrentTeamResponse:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    team = service.update_team(current_user, team_data, session)

    return CurrentTeamResponse.model_validate(team)


@router.delete("/{team_id}", status_code=204)
async def delete_team(
    team_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    if not current_user.is_super_admin:
        raise SuperAdminRequired()

    return service.delete_team(team_id, session)


@router.post("/intention-to-subscribe", status_code=201)
async def create_intention_to_subscribe(
    intention_data: IntentionToSubscribeCreate,
    session: Session = Depends(get_session),
) -> None:
    service.create_intention_to_subscribe(intention_data, session)
