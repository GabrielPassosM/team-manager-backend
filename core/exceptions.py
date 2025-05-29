from dataclasses import dataclass
from fastapi import HTTPException


@dataclass
class AdminRequired(HTTPException):
    status_code = 403
    detail = "Usuário não possui permissão para essa ação."


@dataclass
class SuperAdminRequired(HTTPException):
    status_code = 403
    detail = "You not that important."


@dataclass
class StartDateBiggerThanEnd(HTTPException):
    status_code = 400
    detail = "Data de início maior que data de término"
