from uuid import UUID

from pydantic import BaseModel, field_validator

from bounded_contexts.player.models import PlayerPositions
from core.schemas import BaseSchema


class PlayerResponse(BaseSchema):
    id: UUID
    name: str
    image_url: str | None = None
    shirt_number: int | None = None
    position: PlayerPositions

    # From GameStatsResponse
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


class PlayerUpdate(BaseSchema):
    name: str | None = None
    image_url: str | None = None
    shirt_number: int | None = None
    position: PlayerPositions | None = None


class PlayerFilter(BaseModel):
    name: str | None = None
    shirt_number: int | None = None
    positions: list[PlayerPositions] | None = None

    order_by: str | None = None

    @property
    def is_empty(self) -> bool:
        return all(
            value is None or (isinstance(value, list) and not value)
            for value in self.model_dump().values()
        )

    @field_validator("order_by")
    @classmethod
    def validate_order_by_options(cls, v):
        if v is None:
            return v
        options = ["name_asc", "name_desc", "shirt_number_asc", "shirt_number_desc"]
        if v not in options:
            raise ValueError(f"order_by must be one of {options}")
        return v


class PlayerNameAndShirt(BaseSchema):
    id: UUID
    name: str
    shirt_number: int | None = None

    @field_validator("name")
    @classmethod
    def name_max_size(cls, v):
        return v[:25]


class PlayerWithoutUserResponse(PlayerNameAndShirt):
    pass
