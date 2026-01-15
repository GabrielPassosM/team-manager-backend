from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class TermsNotFound(HTTPException):
    status_code = 404
    detail = "Termos de uso não encontrados."
