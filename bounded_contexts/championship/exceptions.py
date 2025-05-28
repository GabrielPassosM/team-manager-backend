from dataclasses import dataclass

from fastapi import HTTPException


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
