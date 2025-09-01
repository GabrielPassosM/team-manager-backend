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


class IntentionToSubscribe(BaseTable, table=True):
    __tablename__ = "intention_to_subscribe"

    user_name: str = Field(min_length=1, max_length=255)
    user_email: str = Field(min_length=5, max_length=255)
    phone_number: str = Field(min_length=5, max_length=20)
    team_name: str = Field(min_length=1, max_length=255)
