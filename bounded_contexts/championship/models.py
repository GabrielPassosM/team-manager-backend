from datetime import date
from enum import Enum
from uuid import UUID

from sqlmodel import Field

from core.models.base import BaseTable
from libs.datetime import brasilia_now


class ChampionshipStatus(str, Enum):
    NAO_INICIADO = "não iniciado"
    EM_ANDAMENTO = "em andamento"
    FINALIZADO = "finalizado"


class FinalStageOptions(str, Enum):
    FASE_DE_GRUPOS = "fase_de_grupos"
    TRIANGULAR = "triangular"
    REPESCAGEM = "repescagem"
    DECIMA_SEXTAS_DE_FINAL = "decima_sextas_de_final"
    OITAVAS_DE_FINAL = "oitavas_de_final"
    QUARTAS_DE_FINAL = "quartas_de_final"
    SEMI_FINAL = "semi_final"
    VICE_CAMPEAO = "vice_campeao"
    CAMPEAO = "campeao"


class Championship(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id", index=True)
    name: str = Field(min_length=1, max_length=255)
    start_date: date = Field()
    end_date: date | None = Field(nullable=True, default=None)

    is_league_format: bool = Field(index=True)

    # is_league_format == False
    final_stage: str | None = Field(
        nullable=True, default=None, max_length=100
    )  # FinalStageOptions
    # is_league_format == True
    final_position: int | None = Field(nullable=True, default=None, ge=1, le=200)

    @property
    def status(self) -> ChampionshipStatus:
        today = brasilia_now().date()
        if self.start_date > today:
            return ChampionshipStatus.NAO_INICIADO
        elif self.end_date and self.end_date < today:
            return ChampionshipStatus.FINALIZADO
        else:
            return ChampionshipStatus.EM_ANDAMENTO
