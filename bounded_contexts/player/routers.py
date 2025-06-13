from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from bounded_contexts.player import service
from bounded_contexts.player.schemas import (
    PlayerResponse,
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerWithoutUserResponse,
)
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
    player = service.create_player(create_data, current_user, session)
    return PlayerResponse.model_validate(player)


@router.get("/", status_code=200)
async def get_players(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    players = service.get_players_by_team(
        current_user.team_id, current_user.player_id, session
    )
    if current_user.player:
        players.insert(0, current_user.player)

    return [PlayerResponse.model_validate(player) for player in players]


@router.get("/without-user", status_code=200)
async def get_players_without_user(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerWithoutUserResponse]:
    if not current_user.has_admin_privileges:
        raise AdminRequired()

    players = service.get_players_without_user(current_user.team_id, session)

    return [PlayerWithoutUserResponse.model_validate(player) for player in players]


@router.patch("/{player_id}", status_code=200)
async def update_player(
    player_id: UUID,
    update_data: PlayerUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> PlayerResponse:
    player_updated = service.update_player(
        player_id, update_data, session, current_user
    )
    return PlayerResponse.model_validate(player_updated)


@router.delete("/{player_id}", status_code=204)
async def delete_player(
    player_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
):
    service.delete_player(player_id, session, current_user)


@router.post("/filter", status_code=200)
async def filter_players(
    filter_data: PlayerFilter,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[PlayerResponse]:
    if filter_data.is_empty:
        players = service.get_players_by_team(current_user.team_id, session)
    else:
        players = service.filter_players(current_user.team_id, filter_data, session)
    return [PlayerResponse.model_validate(player) for player in players]
