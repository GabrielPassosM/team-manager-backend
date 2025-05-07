from uuid import UUID
from sqlmodel import Session

import bcrypt

from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.exceptions import UserNotFound, EmailAlreadyInUse
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserWriteRepo, UserReadRepo
from bounded_contexts.user.schemas import UserCreate
from core.settings import PASSWORD_PEPPER, SALT_ROUNDS


def _hash_password(password: str) -> str:
    peppered_password = (PASSWORD_PEPPER + password).encode()
    hashed_password = bcrypt.hashpw(
        peppered_password, bcrypt.gensalt(rounds=SALT_ROUNDS)
    )
    return hashed_password.decode()


def create_user(user_data: UserCreate, session: Session) -> User:
    if not TeamReadRepo(session=session).get_by_id(user_data.team_id):
        raise TeamNotFound()

    if UserReadRepo(session=session).get_by_email_and_team(
        user_data.team_id, user_data.email
    ):
        raise EmailAlreadyInUse()

    hashed_password = _hash_password(user_data.password)

    return UserWriteRepo(session=session).save(user_data, hashed_password)


def get_user_by_id(user_id: UUID, session: Session) -> User:
    user = UserReadRepo(session=session).get_by_id(user_id)
    if not user:
        raise UserNotFound()

    return user


def get_users_by_team(team_id: UUID, session: Session) -> list[User]:
    users = UserReadRepo(session=session).get_all_by_team_id(team_id)
    return users


def delete_user(user_id: UUID, session: Session) -> None:
    user = get_user_by_id(user_id, session)
    UserWriteRepo(session=session).delete(user)
