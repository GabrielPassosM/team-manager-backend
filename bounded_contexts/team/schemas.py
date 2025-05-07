from datetime import date

from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    emblem_url: str | None = None
    foundation_date: date | None = None
    paid_until: date | None = None
