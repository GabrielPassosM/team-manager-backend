from dataclasses import dataclass

from fastapi import HTTPException

from core.settings import FRIENDLY_CHAMPIONSHIP_NAME


@dataclass
class ChampionshipAlreadyExists(HTTPException):
    status_code = 400
    detail = "Já existe um campeonato com este nome cadastrado no sistema"


@dataclass
class ChampionshipNotFound(HTTPException):
    status_code = 404
    detail = "Campeonato não encontrado no sistema"


@dataclass
class FinalAttributeWithoutEndDate(HTTPException):
    status_code = 400
    detail = "Para ter colocação final, o campeonato deve ter data de término"


@dataclass
class LeagueFormatCantHaveFinalStage(HTTPException):
    status_code = 400
    detail = "Campeonato de pontos corridos deve ter colocação final em número, e não em estágio"


@dataclass
class KnockOutCantHaveFinalPosition(HTTPException):
    status_code = 400
    detail = "Campeonato mata-mata deve ter colocação final em estágio, e não em número"


@dataclass
class CantEditFriendlyChampionship(HTTPException):
    status_code = 400
    detail = f"Não é possível editar o campeonato {FRIENDLY_CHAMPIONSHIP_NAME}"


@dataclass
class CantDeleteFriendlyChampionship(HTTPException):
    status_code = 400
    detail = f"Não é possível deletar o campeonato {FRIENDLY_CHAMPIONSHIP_NAME}"
