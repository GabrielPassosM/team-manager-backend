from uuid import UUID

from fastapi import APIRouter, Depends
from sqlmodel import Session

from bounded_contexts.game_and_stats.stats import service
from bounded_contexts.game_and_stats.stats.schemas import GameStatsResponse
from bounded_contexts.user.models import User
from core.services.auth import validate_user_token
from infra.database import get_session

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/{game_id}", status_code=200)
async def get_games_stats(
    game_id: UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(validate_user_token),
) -> GameStatsResponse:
    return service.get_game_stats(game_id, session)
