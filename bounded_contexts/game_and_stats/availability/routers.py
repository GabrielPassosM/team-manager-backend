from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from bounded_contexts.game_and_stats.availability import service
from bounded_contexts.game_and_stats.availability.schemas import (
    GamePlayerAvailabilityCreate,
    GamePlayersAvailabilityResponse,
    GamePlayerAvailabilityUpdate,
)
from bounded_contexts.user.models import User
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/player-availability", tags=["Player Availability"])


@router.post("/", status_code=201)
async def create_game_player_availability(
    create_data: GamePlayerAvailabilityCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.create_game_player_availability(create_data, session, current_user)


@router.get("/{game_id}", status_code=200)
async def get_game_players_availability(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> GamePlayersAvailabilityResponse:
    return service.get_game_players_availability(game_id, session, current_user)


@router.patch("/{game_id}", status_code=200)
async def update_game_player_availability(
    game_id: UUID,
    update_data: GamePlayerAvailabilityUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.update_game_player_availability(
        update_data, game_id, session, current_user
    )


@router.delete("/{game_id}", status_code=204)
async def delete_game_player_availability(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.delete_game_player_availability(game_id, session, current_user)
