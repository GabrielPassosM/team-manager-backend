from datetime import date
from uuid import UUID

from pydantic import BaseModel, model_validator

from bounded_contexts.championship.models import ChampionshipStatus, FinalStageOptions
from core.schemas import BaseSchema


class ChampionshipCreate(BaseModel):
    name: str
    start_date: date | None = None
    end_date: date | None = None
    is_league_format: bool
    final_stage: FinalStageOptions | None = None
    final_position: int | None = None

    @model_validator(mode="after")
    def check_dates_and_league_format(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be later or equal than start_date")

        if (self.final_stage or self.final_position) and not self.end_date:
            raise ValueError(
                "Final stage/position can only be set if end_date is provided"
            )

        if self.is_league_format and self.final_stage:
            raise ValueError(
                "Final stage cannot be set for league format championships"
            )

        if not self.is_league_format and self.final_position:
            raise ValueError(
                "Final position cannot be set for non-league format championships"
            )

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
