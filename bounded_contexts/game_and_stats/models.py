from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID
from datetime import datetime

from sqlmodel import Field, Relationship

from core.consts import DEFAULT_ADVERSARY
from core.models.base import BaseTable

if TYPE_CHECKING:
    from bounded_contexts.championship.models import Championship
    from bounded_contexts.player.models import Player


class Game(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id")
    championship_id: UUID = Field(foreign_key="championship.id")
    adversary: str = Field(min_length=1, max_length=255, default=DEFAULT_ADVERSARY)
    date_hour: datetime = Field()
    round: int | None = Field(ge=1, le=10000, nullable=True, default=None)
    stage: str | None = Field(
        nullable=True, default=None, max_length=100
    )  # StageOptions
    is_home: bool = Field(default=True)
    is_wo: bool = Field(default=False)
    team_score: int | None = Field(ge=0, le=100, nullable=True, default=None)
    adversary_score: int | None = Field(ge=0, le=100, nullable=True, default=None)
    team_penalty_score: int | None = Field(ge=0, le=100, nullable=True, default=None)
    adversary_penalty_score: int | None = Field(
        ge=0, le=100, nullable=True, default=None
    )

    championship: "Championship" = Relationship(back_populates="game")


class AvailabilityStatus(str, Enum):
    IN = "in"
    OUT = "out"
    DOUBT = "doubt"


class GamePlayerAvailability(BaseTable, table=True):
    __tablename__ = "game_player_availability"

    team_id: UUID = Field(foreign_key="team.id")
    game_id: UUID = Field(foreign_key="game.id")
    player_id: UUID = Field(foreign_key="player.id")
    status: str = Field(min_length=1, max_length=10)  # AvailabilityStatus


class StatOptions(str, Enum):
    PLAYED = "played"
    GOAL = "goal"
    ASSIST = "assist"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    MVP = "mvp"


class GamePlayerStat(BaseTable, table=True):
    __tablename__ = "game_player_stat"

    team_id: UUID = Field(foreign_key="team.id")
    game_id: UUID = Field(foreign_key="game.id")
    # Nullable for own goals
    player_id: UUID | None = Field(foreign_key="player.id", nullable=True)
    # Used to bound goal and assist
    related_stat_id: UUID | None = Field(
        foreign_key="game_player_stat.id", nullable=True
    )

    stat: str = Field(min_length=1, max_length=50)  # StatOptions
    quantity: int

    player: Optional["Player"] = Relationship(back_populates="game_player_stat")
