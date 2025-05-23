from uuid import UUID
from sqlmodel import Session

from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.exceptions import (
    UserNotFound,
    EmailAlreadyInUse,
    LoginUnauthorized,
)
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserWriteRepo, UserReadRepo
from bounded_contexts.user.schemas import UserCreate
from core.services.password import verify_password, hash_password


def authenticate_user(email: str, password: str, session: Session) -> User:
    user = UserReadRepo(session=session).get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        raise LoginUnauthorized()

    return user


def create_user(user_data: UserCreate, team_id: UUID, session: Session) -> User:
    if not TeamReadRepo(session=session).get_by_id(team_id):
        raise TeamNotFound()

    if UserReadRepo(session=session).get_by_email(user_data.email):
        raise EmailAlreadyInUse()

    hashed_password = hash_password(user_data.password)

    return UserWriteRepo(session=session).save(user_data, team_id, hashed_password)


def get_user_by_id(user_id: UUID, session: Session) -> User:
    user = UserReadRepo(session=session).get_by_id(user_id)
    if not user:
        raise UserNotFound()

    return user


def get_users_by_team(team_id: UUID, session: Session) -> list[User]:
    users = UserReadRepo(session=session).get_by_team_id_excluding_super_admin(team_id)
    return users


def delete_user(user_id: UUID, session: Session) -> None:
    user = get_user_by_id(user_id, session)
    UserWriteRepo(session=session).delete(user)
