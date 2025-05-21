import re
from datetime import date

from pydantic import BaseModel, model_validator, field_validator

from core.consts import DEFAULT_PRIMARY_COLOR


class _TeamBase(BaseModel):
    name: str
    emblem_url: str | None = None
    foundation_date: date | None = None
    season_start_date: date | None = None
    season_end_date: date | None = None
    primary_color: str | None = DEFAULT_PRIMARY_COLOR

    @model_validator(mode="after")
    def check_season_dates(self):
        if self.season_start_date and self.season_end_date:
            if self.season_end_date <= self.season_start_date:
                raise ValueError("season_end_date must be later than season_start_date")
        return self

    @field_validator("primary_color")
    @classmethod
    def validate_hex_color(cls, v):
        if v is None:
            return v
        if not re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", v):
            raise ValueError("primary_color must be a valid hex color code")
        return v


class TeamCreate(_TeamBase):
    paid_until: date | None = None


class TeamUpdate(_TeamBase):
    pass


class CurrentTeamResponse(_TeamBase):
    paid_until: date
