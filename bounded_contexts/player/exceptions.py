from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class PlayerNotFound(HTTPException):
    status_code = 404
    detail = "Jogador não encontrado no sistema"
