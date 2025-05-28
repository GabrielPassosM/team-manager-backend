from datetime import date
from uuid import UUID

from pydantic import BaseModel, model_validator

from bounded_contexts.championship.exceptions import (
    FinalAttributeWithoutEndDate,
    KnockOutCantHaveFinalPosition,
    LeagueFormatCantHaveFinalStage,
)
from bounded_contexts.championship.models import ChampionshipStatus, FinalStageOptions
from core.exceptions import StartDateBiggerThanEnd
from core.schemas import BaseSchema


class _ChampionshipBase(BaseModel):
    name: str
    start_date: date
    end_date: date | None = None
    is_league_format: bool
    final_stage: FinalStageOptions | None = None
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
    final_stage: FinalStageOptions | None = None
    final_position: int | None = None
    status: ChampionshipStatus


class ChampionshipCreate(_ChampionshipBase):
    pass


class ChampionshipUpdate(BaseSchema, _ChampionshipBase):
    pass
