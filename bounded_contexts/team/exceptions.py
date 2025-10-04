from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class TeamNotFound(HTTPException):
    status_code = 404
    detail = "Time não encontrado no sistema"


@dataclass
class TeamNotFoundByCode(HTTPException):
    status_code = 404
    detail = "Time não encontrado no sistema. Por favor, verifique o código e tente novamente."


@dataclass
class TeamSubscriptionExpired(HTTPException):
    status_code = 403
    detail = "A assinatura do time expirou."
    is_admin: bool

    def __post_init__(self):
        if self.is_admin:
            self.detail += " Renove sua assinatura para continuar utilizando o sistema."
        else:
            self.detail += (
                " Entre em contato com um administrador do seu time para renová-la."
            )
