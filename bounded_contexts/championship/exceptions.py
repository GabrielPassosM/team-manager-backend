from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class ChampionshipAlreadyExists(HTTPException):
    status_code = 400
    detail = "Já existe um campeonato com este nome cadastrado no sistema"
