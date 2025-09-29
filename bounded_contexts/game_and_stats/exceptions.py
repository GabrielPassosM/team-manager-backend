from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException

from core.settings import BEFORE_SYSTEM_CHAMPIONSHIP_NAME


@dataclass
class GameDateOutsideChampionshipRange(HTTPException):
    champ_date_range: tuple[date, date | None]
    status_code = 400
    detail = f"A data do jogo deve estar dentro da duração do campeonato"

    def __post_init__(self):
        formated_end = "indefinido"
        if self.champ_date_range[1]:
            formated_end = self.champ_date_range[1].strftime("%d/%m/%y")

        self.detail += (
            f" ({self.champ_date_range[0].strftime("%d/%m/%y")} - {formated_end})."
        )


@dataclass
class SomePlayersNotFound(HTTPException):
    status_code = 404
    detail = f"Alguns jogadores selecionados não foram encontrados no sistema. Por favor entre em contato com o suporte."


@dataclass
class InvalidChampionshipFormat(HTTPException):
    status_code = 400
    detail = f"Etapa do jogo não compatível com tipo de campeonato (liga ou mata-mata)."


@dataclass
class StatPlayerNotInGamePlayers(HTTPException):
    status_code = 400
    detail = (
        f"Jogador selecionado para estatística não está entre os jogadores da partida."
    )


@dataclass
class InvalidYellowCardsQuantity(HTTPException):
    status_code = 400
    detail = f"Quantidade de cartões amarelos não pode ser maior que 2."


@dataclass
class GameNotFound(HTTPException):
    status_code = 404
    detail = f"Jogo não encontrado no sistema."


@dataclass
class UserNeedsAssociatedPlayer(HTTPException):
    status_code = 400
    detail = f"Usuário precisa estar associado a um jogador para realizar esta ação."
    is_admin: bool

    def __post_init__(self):
        if self.is_admin:
            self.detail += " Acesse a página de usuários para fazer a associação."
        else:
            self.detail += (
                " Entre em contato com um administrador para fazer a associação."
            )


@dataclass
class AvailabilityNotFound(HTTPException):
    status_code = 404
    detail = f"Disponibilidade não encontrada para o jogador no jogo selecionado."


@dataclass
class CantCreateGamesInBeforeSystemChampionship(HTTPException):
    status_code = 400
    detail = (
        f"Não é possível criar jogos no campeonato {BEFORE_SYSTEM_CHAMPIONSHIP_NAME}."
    )
