from datetime import date, timedelta

from sqlmodel import Field

from core.models.base import BaseTable


def _default_paid_until():
    return date.today() + timedelta(days=30)


class Team(BaseTable, table=True):
    name: str = Field(min_length=1, max_length=255)
    emblem_url: str | None = Field(nullable=True, default=None)
    foundation_date: date | None = Field(nullable=True, default=None)
    paid_until: date = Field(default_factory=_default_paid_until)
