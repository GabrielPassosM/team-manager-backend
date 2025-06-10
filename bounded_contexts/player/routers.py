from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from bounded_contexts.player import service
from bounded_contexts.player.schemas import PlayerResponse, PlayerCreate, PlayerUpdate
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/players", tags=["Player"])


@router.post("/", status_code=201)
async def create_player(
    create_data: PlayerCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> PlayerResponse:
    # TODO or current_user DOES NOT have a linked player yet
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    player = service.create_player(create_data, current_user, session)
    return PlayerResponse.model_validate(player)


@router.get("/", status_code=200)
async def get_players(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    players = service.get_players_by_team(current_user.team_id, session)

    return [PlayerResponse.model_validate(champ) for champ in players]


@router.patch("/{player_id}", status_code=200)
async def update_player(
    player_id: UUID,
    update_data: PlayerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> PlayerResponse:
    # TODO or current_user linked to player
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    player = service.update_player(player_id, update_data, session, current_user.id)
    return PlayerResponse.model_validate(player)


@router.delete("/{player_id}", status_code=204)
async def delete_player(
    player_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
):
    # TODO or current_user linked to player
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    service.delete_player(player_id, session, current_user.id)
