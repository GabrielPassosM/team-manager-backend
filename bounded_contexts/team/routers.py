from fastapi import APIRouter

from bounded_contexts.team import service
from bounded_contexts.team.models import Team
from bounded_contexts.team.schemas import TeamCreate
from libs.base_types.uuid import BaseUUID


router = APIRouter(prefix="/teams", tags=["Team"])


@router.post("/", status_code=201)
async def create_team(
    team_data: TeamCreate,
) -> Team:
    return service.create_team(team_data)


@router.get("/{team_id}", status_code=200)
async def get_team(team_id: BaseUUID) -> Team:
    return service.get_team_by_id(team_id)


@router.delete("/{team_id}", status_code=204)
async def delete_team(team_id: BaseUUID) -> None:
    return service.delete_team(team_id)
