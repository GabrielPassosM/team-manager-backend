from uuid import UUID
from sqlmodel import Session

from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.exceptions import (
    UserNotFound,
    EmailAlreadyInUse,
    LoginUnauthorized,
    CantUpdateAdminUser,
    CantDeleteYourself,
)
from bounded_contexts.user.models import User
from bounded_contexts.user.repo import UserWriteRepo, UserReadRepo
from bounded_contexts.user.schemas import UserCreate, UserUpdate
from core.exceptions import AdminRequired
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


def update_user(
    user_id: UUID, user_data: UserUpdate, session: Session, current_user: User
) -> User:
    user_to_update = UserReadRepo(session=session).get_by_id(user_id)
    if not user_to_update:
        raise UserNotFound()

    _validate_update_request(current_user, user_to_update, user_data)

    if user_data.email != user_to_update.email and UserReadRepo(
        session=session
    ).get_by_email(user_data.email):
        raise EmailAlreadyInUse()

    if all(
        [
            not user_data.password,
            user_to_update.name == user_data.name,
            user_to_update.email == user_data.email,
        ]
    ):
        return user_to_update

    return UserWriteRepo(session=session).update(
        user_to_update, user_data, current_user.id
    )


def _validate_update_request(
    current_user: User, user_to_update: User, user_data: UserUpdate
) -> None:
    if current_user.is_super_admin or current_user.id == user_to_update.id:
        return

    # Cannot update other users' passwords
    if user_data.password:
        raise AdminRequired()

    # Cannot update other user if not admin
    if not current_user.is_admin:
        raise AdminRequired()

    # Only super admin can update other admin
    if user_to_update.is_admin:
        raise CantUpdateAdminUser()


def get_user_by_id(user_id: UUID, session: Session) -> User:
    user = UserReadRepo(session=session).get_by_id(user_id)
    if not user:
        raise UserNotFound()

    return user


def get_users_by_team(current_user: User, session: Session) -> list[User]:
    users = UserReadRepo(
        session=session
    ).get_by_team_excluding_super_admin_and_current_user(
        current_user.team_id, current_user.id
    )
    return users


def delete_user(user_id: UUID, current_user: User, session: Session) -> None:
    user_to_delete = get_user_by_id(user_id, session)
    if not user_to_delete:
        raise UserNotFound()

    _validate_delete_request(current_user, user_to_delete)

    UserWriteRepo(session=session).delete(user_to_delete, current_user.id)


def _validate_delete_request(current_user: User, user_to_delete: User) -> None:
    if current_user.id == user_to_delete.id:
        raise CantDeleteYourself()

    if current_user.is_super_admin:
        return

    if not current_user.is_admin:
        raise AdminRequired()

    if user_to_delete.has_admin_privileges:
        raise CantUpdateAdminUser()
