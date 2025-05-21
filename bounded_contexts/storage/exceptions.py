from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class FailedUploadStorage(HTTPException):
    status_code = 500
    detail = "Erro ao salvar a imagem do emblema. Por favor, tente novamente."
