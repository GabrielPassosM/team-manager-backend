from uuid import UUID

from pydantic import BaseModel


class GameStatsResponse(BaseModel):
    players: list[list[str | int | None]]
    goals_and_assists: list[dict[str, str | None]]
    yellow_cards: list[list[str | int]]
    red_cards: list[str]
    mvps: list[list[str | int]]


class MonthTopScorerResponse(BaseModel):
    id: UUID
    name: str
    image_url: str | None
    shirt: int | None
    goals: int
    games_played: int
