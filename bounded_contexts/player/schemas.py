from uuid import UUID

from pydantic import BaseModel

from bounded_contexts.player.models import PlayerPositions
from core.schemas import BaseSchema


class PlayerResponse(BaseSchema):
    id: UUID
    name: str
    image_url: str | None = None
    shirt_number: int | None = None
    position: PlayerPositions

    # From PlayerStatLog
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    mvps: int = 0


class PlayerCreate(BaseModel):
    id: UUID | None = None
    name: str
    image_url: str | None = None
    shirt_number: int | None = None
    position: PlayerPositions
