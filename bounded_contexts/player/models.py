from enum import Enum
from uuid import UUID

from sqlmodel import Field

from core.models.base import BaseTable


class PlayerPositions(str, Enum):
    # Futebol Campo e Society
    GOLEIRO = "Goleiro"
    ZAGUEIRO = "Zagueiro"
    LATERAL = "Lateral"
    LATERAL_DIREITO = "Lateral-direito"
    LATERAL_ESQUERDO = "Lateral-esquerdo"
    MEIO_CAMPO = "Meio-campo"
    VOLANTE = "Volante"
    MEIA_DIREITA = "Meia-direita"
    MEIA_ESQUERDA = "Meia-esquerda"
    ATACANTE = "Atacante"
    PONTA = "Ponta"
    PONTA_DIREITA = "Ponta-direita"
    PONTA_ESQUERDA = "Ponta-esquerda"

    # Futsal
    FIXO = "Fixo"
    ALA = "Ala"
    PIVO = "Pivô"


class Player(BaseTable, table=True):
    team_id: UUID = Field(foreign_key="team.id", index=True)
    name: str = Field(min_length=1, max_length=255)
    image_url: str | None = Field(nullable=True, default=None)
    shirt_number: int | None = Field(nullable=True, default=None)
    position: str  # PlayerPositions enum
