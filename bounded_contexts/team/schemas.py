from pydantic import BaseModel


class TeamCreate(BaseModel):
    name: str
    emblem_url: str | None = None
    foundation_date: str | None = None
    paid_until: str | None = None
