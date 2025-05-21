from datetime import date

from sqlmodel import Field

from core.consts import DEFAULT_PRIMARY_COLOR
from core.models.base import BaseTable
from libs.datetime import this_day_next_month


class Team(BaseTable, table=True):
    name: str = Field(min_length=1, max_length=255)
    emblem_url: str | None = Field(nullable=True, default=None)
    foundation_date: date | None = Field(nullable=True, default=None)
    paid_until: date = Field(default_factory=this_day_next_month)
    season_start_date: date | None = Field(nullable=True, default=None)
    season_end_date: date | None = Field(nullable=True, default=None)
    primary_color: str | None = Field(nullable=True, default=DEFAULT_PRIMARY_COLOR)
