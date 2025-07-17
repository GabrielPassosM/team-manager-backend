from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from bounded_contexts.game_and_stats.game import service
from bounded_contexts.game_and_stats.game.schemas import (
    GameCreate,
    GamesPageResponse,
    GameUpdate,
    GameAndStatsToUpdateResponse,
    GameFilter,
    NextGameResponse,
    LastGameResponse,
)
from bounded_contexts.user.models import User
from core.exceptions import AdminRequired
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/games", tags=["Game"])


@router.post("/", status_code=201)
async def create_game_and_stats(
    create_data: GameCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> UUID:
    return service.create_game_and_stats(create_data, current_user, session)


@router.post("/filter", status_code=200)
async def get_games_filtered_and_paginated(
    filter_data: GameFilter,
    limit: int = Query(5, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> GamesPageResponse:
    return service.get_games_filtered_and_paginated(
        current_user.team_id, filter_data, limit, offset, session
    )


@router.get("/to-update/{game_id}", status_code=200)
async def get_game_and_stats_to_update(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> GameAndStatsToUpdateResponse:
    if not current_user.has_admin_privileges:
        raise AdminRequired()
    return service.get_game_and_stats_to_update(game_id, session)


@router.patch("/{game_id}", status_code=200)
async def update_game_and_stats(
    game_id: UUID,
    update_data: GameUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.update_game_and_stats(game_id, update_data, current_user, session)


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.delete_game_and_dependent_tables(game_id, current_user, session)


@router.post("/reactivate/{game_id}", status_code=201)
async def reactivate_game(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> None:
    return service.reactivate_game_and_stats(game_id, current_user, session)


@router.get("/next-game", status_code=200)
async def get_next_game(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> NextGameResponse | None:
    """Dashboard endpoint"""
    return service.get_next_game(current_user.team_id, session)


@router.get("/last-games", status_code=200)
async def get_last_games(
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> list[LastGameResponse] | None:
    """Dashboard endpoint"""
    return service.get_last_games(current_user.team_id, session)
