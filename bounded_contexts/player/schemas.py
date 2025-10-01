from uuid import UUID

from pydantic import BaseModel, field_validator

from bounded_contexts.game_and_stats.models import StatOptions
from bounded_contexts.player.models import PlayerPositions
from core.enums import StageOptions
from core.schemas import BaseSchema, StatsSchema
from libs.schemas import NumberRangeSchema, DateRangeSchema


class PlayerResponse(BaseSchema, StatsSchema):
    id: UUID
    name: str
    image_url: str | None = None
    shirt_number: int | None = None
    position: PlayerPositions


class PlayerCreate(StatsSchema):
    # TODO see why front is sending id
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


class PlayersStatsFilter(BaseModel):
    # Stat related
    stat_name: StatOptions | None = StatOptions.GOAL
    order_by: str | None = None
    quantity_range: NumberRangeSchema | None = None

    # Game/championship related
    date_range: DateRangeSchema | None = None
    championships: list[UUID] | None = None
    stages: list[StageOptions] | None = None
    exclude_friendly: bool = True

    # Player related
    players: list[UUID] | None = None
    player_positions: list[PlayerPositions] | None = None

    @field_validator("order_by")
    @classmethod
    def validate_order_by_options(cls, v):
        if v is None:
            return v
        options = ["asc", "desc"]
        if v not in options:
            raise ValueError(f"order_by must be one of: {options}")
        return v
