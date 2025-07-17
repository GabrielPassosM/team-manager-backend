from datetime import datetime, date
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, model_validator, field_validator

from bounded_contexts.game_and_stats.models import GameResult
from core.enums import StageOptions
from core.schemas import BaseSchema


class GoalAndAssist(BaseModel):
    goal_player_id: UUID | None  # None for own goals
    assist_player_id: UUID | None = None


class PlayerAndQuantity(BaseModel):
    player_id: UUID
    quantity: int


class NameAndId(BaseModel):
    id: UUID
    name: str


class GameInfoIn(BaseModel):
    championship_id: UUID
    adversary: str
    date_hour: datetime
    round: int | None = None
    stage: StageOptions | None = None
    is_home: bool = True
    is_wo: bool = False
    team_score: int | None = None
    adversary_score: int | None = None
    team_penalty_score: int | None = None
    adversary_penalty_score: int | None = None

    @field_validator("date_hour")
    @classmethod
    def validate_date_hour(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            # TODO add timezone config in Team
            value = value.replace(tzinfo=ZoneInfo("America/Sao_Paulo"))
        return value


class GameStatsIn(BaseModel):
    players: list[UUID] | None = None
    goals_and_assists: list[GoalAndAssist] | None = None
    yellow_cards: list[PlayerAndQuantity] | None = None
    red_cards: list[UUID] | None = None
    mvps: list[PlayerAndQuantity] | None = None


class _GameBase(GameInfoIn, GameStatsIn):
    @model_validator(mode="after")
    def make_validations_and_sanitize(self):
        if len(self.adversary) < 1 or len(self.adversary) > 255:
            raise ValueError("Adversary must be between 1 and 255 characters long.")
        if self.round is not None and (self.round < 1 or self.round > 10000):
            raise ValueError("Round must be between 1 and 10000 if provided.")
        if self.stage and self.round:
            raise ValueError("Can't have both stage and round")
        if self.is_wo:
            self.team_score = 3
            self.adversary_score = 0
            self.team_penalty_score = None
            self.adversary_penalty_score = None
            self.players = None
            self.goals_and_assists = None
            self.yellow_cards = None
            self.red_cards = None
            self.mvps = None
            return self

        if (self.team_score is not None and self.adversary_score is None) or (
            self.team_score is None and self.adversary_score is not None
        ):
            raise ValueError("Must have both team_score and adversary_score or neither")
        if (
            self.team_penalty_score is not None and self.adversary_penalty_score is None
        ) or (
            self.team_penalty_score is None and self.adversary_penalty_score is not None
        ):
            raise ValueError(
                "Must have both team_penalty_score and adversary_penalty_score or neither"
            )
        if self.players:
            self.players = list(set(self.players))
        if self.red_cards:
            self.red_cards = list(set(self.red_cards))
        if self.team_score is not None and (
            self.team_score < 0 or self.team_score > 100
        ):
            raise ValueError("Team score must be between 0 and 100 if provided.")
        if self.adversary_score is not None and (
            self.adversary_score < 0 or self.adversary_score > 100
        ):
            raise ValueError("Adversary score must be between 0 and 100 if provided.")
        if self.team_penalty_score is not None and (
            self.team_penalty_score < 0 or self.team_penalty_score > 100
        ):
            raise ValueError(
                "team_penalty_score must be between 0 and 100 if provided."
            )
        if self.adversary_penalty_score is not None and (
            self.adversary_penalty_score < 0 or self.adversary_penalty_score > 100
        ):
            raise ValueError(
                "adversary_penalty_score must be between 0 and 100 if provided."
            )
        if (
            any([self.goals_and_assists, self.yellow_cards, self.red_cards, self.mvps])
            and not self.players
        ):
            raise ValueError("Players must be provided if any stats are included.")
        if (
            self.goals_and_assists
            and self.team_score is not None
            and len(self.goals_and_assists) != self.team_score
        ):
            raise ValueError("Can't have more goals and assists than team_score")
        if self.goals_and_assists:
            for pair in self.goals_and_assists:
                goal = pair.goal_player_id
                assist = pair.assist_player_id
                if assist and not goal:
                    raise ValueError("Can't assist an own goal")
                if assist and goal and assist == goal:
                    raise ValueError("Can't assist and score at the same time bro")

        return self


class GameCreate(_GameBase):
    pass


class GameUpdate(_GameBase):
    has_stats_update: bool


class GameStatsToUpdateResponse(GameStatsIn):
    pass


class GameResponse(BaseSchema):
    id: UUID
    championship: NameAndId
    adversary: str
    date_hour: datetime
    round: int | None
    stage: StageOptions | None
    is_home: bool
    is_wo: bool
    team_score: int | None
    adversary_score: int | None
    team_penalty_score: int | None
    adversary_penalty_score: int | None


class GamesPageResponse(BaseModel):
    items: list[GameResponse]
    total: int
    limit: int
    offset: int


class GameAndStatsToUpdateResponse(GameResponse, GameStatsToUpdateResponse):
    pass


class GameFilter(BaseModel):
    championship_id: UUID | None = None
    adversary: str | None = None
    date_hour_from: datetime | None = None
    date_hour_to: datetime | None = None
    round: int | None = None
    stages: list[StageOptions] | None = None
    is_home: bool | None = None
    is_wo: bool | None = None
    team_score_from: int | None = None
    team_score_to: int | None = None
    adversary_score_from: int | None = None
    adversary_score_to: int | None = None
    has_penalty_score: bool | None = None

    order_by: str | None = None

    @property
    def is_empty(self) -> bool:
        return all(
            value is None or (isinstance(value, list) and not value)
            for value in self.model_dump().values()
        )

    @field_validator("order_by")
    @classmethod
    def validate_order_by_options(cls, v):
        if v is None:
            return v
        options = [
            "date_hour_asc",
            "date_hour_desc",
            "team_score_asc",
            "team_score_desc",
            "adversary_score_asc",
            "adversary_score_desc",
        ]
        if v not in options:
            raise ValueError(f"order_by must be one of {options}")
        return v


class NextGameResponse(BaseModel):
    id: UUID
    championship_name: str
    adversary: str
    date_hour: datetime
    is_home: bool
    confirmed_players: int


class LastGameResponse(BaseModel):
    id: UUID
    date: date
    adversary: str
    team_score: int
    adversary_score: int
    result: GameResult
