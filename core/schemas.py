from pydantic import BaseModel


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True}


class StatsSchema(BaseModel):
    played: int = 0
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    mvps: int = 0
