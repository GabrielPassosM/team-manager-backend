from datetime import date
from typing import Optional

from sqlmodel import Field, Relationship

from core.consts import DEFAULT_PRIMARY_COLOR
from core.models.base import BaseTable
from libs.datetime import add_months_to_date


class Team(BaseTable, table=True):
    name: str = Field(min_length=1, max_length=255)
    emblem_url: str | None = Field(nullable=True, default=None)
    foundation_date: date | None = Field(nullable=True, default=None)
    paid_until: date = Field(default_factory=add_months_to_date)
    max_players_or_users: int = Field(default=30)
    season_start_date: date | None = Field(nullable=True, default=None)
    season_end_date: date | None = Field(nullable=True, default=None)
    primary_color: str | None = Field(nullable=True, default=DEFAULT_PRIMARY_COLOR)

    # Only so the backwards relation works (user.team)
    users: Optional["User"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class IntentionToSubscribe(BaseTable, table=True):
    __tablename__ = "intention_to_subscribe"

    user_name: str = Field(min_length=1, max_length=255)
    user_email: str = Field(min_length=5, max_length=255)
    phone_number: str = Field(min_length=5, max_length=20)
    team_name: str = Field(min_length=1, max_length=255)


from bounded_contexts.user.models import User
