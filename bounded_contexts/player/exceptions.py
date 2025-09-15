from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class PlayerNotFound(HTTPException):
    status_code = 404
    detail = "Jogador não encontrado no sistema"


@dataclass
class PlayersLimitReached(HTTPException):
    status_code = 400
    detail = "O número máximo de jogadores do time foi atingido. Atualize seu plano para adicionar mais jogadores."
