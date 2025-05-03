from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class TeamNotFound(HTTPException):
    status_code = 404
    detail = "Time não encontrado no sistema"
