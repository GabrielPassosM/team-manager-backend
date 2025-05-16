from dataclasses import dataclass
from fastapi import HTTPException


@dataclass
class AdminRequired(HTTPException):
    status_code = 403
    detail = "Usuário não possui permissão para essa ação."
