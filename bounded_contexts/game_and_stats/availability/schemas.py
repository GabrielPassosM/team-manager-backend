from uuid import UUID

from pydantic import BaseModel

from bounded_contexts.game_and_stats.models import AvailabilityStatus


class GamePlayerAvailabilityCreate(BaseModel):
    game_id: UUID
    status: AvailabilityStatus


class GamePlayerAvailabilityUpdate(BaseModel):
    status: AvailabilityStatus


class GamePlayersAvailabilityResponse(BaseModel):
    current_player: AvailabilityStatus | None

    available: list[str]
    not_available: list[str]
    doubt: list[str]
