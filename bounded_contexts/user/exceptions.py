from dataclasses import dataclass

from fastapi import HTTPException


@dataclass
class PasswordToLong(HTTPException):
    status_code = 400
    detail = "Senha deve ter no máximo 72 caracteres"


@dataclass
class UserNotFound(HTTPException):
    status_code = 404
    detail = "Usuário não encontrado no sistema"


@dataclass
class EmailAlreadyInUse(HTTPException):
    status_code = 400
    detail = "Já existe um usuário com este e-mail cadastrado no sistema"


@dataclass
class LoginUnauthorized(HTTPException):
    status_code = 401
    detail = "Email ou senha incorretos"
    headers = {"WWW-Authenticate": "Bearer"}


@dataclass
class CantUpdateAdminUser(HTTPException):
    status_code = 403
    detail = "Não é permitido atualizar outro usuário admin. Qualquer dúvida, entre em contato com o suporte técnico."


@dataclass
class CantDeleteAdminUser(HTTPException):
    status_code = 403
    detail = "Não é permitido remover outro usuário admin. Qualquer dúvida, entre em contato com o suporte técnico."


@dataclass
class CantDeleteYourself(HTTPException):
    status_code = 403
    detail = "Não é permitido remover seu próprio usuário. Qualquer dúvida, entre em contato com o suporte técnico."
