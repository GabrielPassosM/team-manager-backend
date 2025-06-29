from datetime import date
from enum import Enum
from typing import Optional, TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from core.models.base import BaseTable
from libs.base_types.interval import Interval
from libs.datetime import brasilia_now

if TYPE_CHECKING:
    from bounded_contexts.game_and_stats.models import Game


class ChampionshipStatus(str, Enum):
    NAO_INICIADO = "não iniciado"
    EM_ANDAMENTO = "em andamento"
    FINALIZADO = "finalizado"


class ChampionshipFormats(str, Enum):
    KNOCKOUT = "knockout"
    LEAGUE = "league"


class Championship(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id", index=True)
    name: str = Field(min_length=1, max_length=255)
    start_date: date = Field()
    end_date: date | None = Field(nullable=True, default=None)

    is_league_format: bool = Field(index=True)

    # when NOT is_league_format
    final_stage: str | None = Field(
        nullable=True, default=None, max_length=100
    )  # StageOptions
    # when is_league_format
    final_position: int | None = Field(nullable=True, default=None, ge=1, le=200)

    # Only so the backwards relation works (game -> champ)
    game: Optional["Game"] = Relationship(back_populates="championship")

    @property
    def status(self) -> ChampionshipStatus:
        today = brasilia_now().date()
        if self.start_date > today:
            return ChampionshipStatus.NAO_INICIADO
        elif self.end_date and self.end_date < today:
            return ChampionshipStatus.FINALIZADO
        else:
            return ChampionshipStatus.EM_ANDAMENTO

    @property
    def date_range(self) -> tuple[date, date | None]:
        return self.start_date, self.end_date

    def date_is_within_championship(self, date_to_check: date) -> bool:
        return Interval(
            start=self.start_date,
            end=self.end_date,
        ).date_is_in_interval(date_to_check)
