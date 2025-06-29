from datetime import date
from uuid import UUID

from pydantic import BaseModel, model_validator, field_validator

from bounded_contexts.championship.exceptions import (
    FinalAttributeWithoutEndDate,
    KnockOutCantHaveFinalPosition,
    LeagueFormatCantHaveFinalStage,
)
from bounded_contexts.championship.models import (
    ChampionshipStatus,
    ChampionshipFormats,
)
from core.enums import StageOptions
from core.exceptions import StartDateBiggerThanEnd
from core.schemas import BaseSchema


class _ChampionshipBase(BaseModel):
    name: str
    start_date: date
    end_date: date | None = None
    is_league_format: bool
    final_stage: StageOptions | None = None
    final_position: int | None = None

    @model_validator(mode="after")
    def check_dates_and_league_format(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise StartDateBiggerThanEnd()

        if (self.final_stage or self.final_position) and not self.end_date:
            raise FinalAttributeWithoutEndDate()

        if self.is_league_format and self.final_stage:
            raise LeagueFormatCantHaveFinalStage()

        if not self.is_league_format and self.final_position:
            raise KnockOutCantHaveFinalPosition()

        return self


class ChampionshipResponse(BaseSchema):
    id: UUID
    team_id: UUID
    name: str
    start_date: date
    end_date: date | None = None
    is_league_format: bool
    final_stage: StageOptions | None = None
    final_position: int | None = None
    status: ChampionshipStatus


class ChampionshipCreate(_ChampionshipBase):
    pass


class ChampionshipUpdate(BaseSchema, _ChampionshipBase):
    pass


class ChampionshipFilter(BaseModel):
    name: str | None = None
    status: list[ChampionshipStatus] | None = None
    start_date_from: date | None = None
    start_date_to: date | None = None
    end_date_from: date | None = None
    end_date_to: date | None = None
    format: ChampionshipFormats | None = None
    final_position_from: int | None = None
    final_position_to: int | None = None
    final_stages: list[StageOptions] | None = None

    order_by: str | None = None

    @property
    def is_empty(self) -> bool:
        return all(
            value is None or (isinstance(value, list) and not value)
            for value in self.model_dump().values()
        )

    @model_validator(mode="after")
    def validate_status_and_dates_are_exclusionary(self):
        if self.status and any(
            [
                self.start_date_to,
                self.start_date_from,
                self.end_date_to,
                self.end_date_from,
            ]
        ):
            raise ValueError("status and date filters are mutually exclusive.")
        return self

    @field_validator("order_by")
    @classmethod
    def validate_order_by_options(cls, v):
        if v is None:
            return v
        options = ["start_date_asc", "start_date_desc", "end_date_asc", "end_date_desc"]
        if v not in options:
            raise ValueError(f"order_by must be one of {options}")
        return v
