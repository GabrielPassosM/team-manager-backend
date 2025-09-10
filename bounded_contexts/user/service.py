import secrets
from datetime import timedelta
from uuid import UUID
from sqlmodel import Session
from loguru import logger

from bounded_contexts.team.exceptions import TeamNotFound
from bounded_contexts.team.repo import TeamReadRepo
from bounded_contexts.user.exceptions import (
    UserNotFound,
    EmailAlreadyInUse,
    LoginUnauthorized,
    CantUpdateAdminUser,
    CantDeleteYourself,
    PlayerAlreadyHasUser,
)
from bounded_contexts.user.models import User, UserPermissions
from bounded_contexts.user.logged_user.models import LoggedUser
from bounded_contexts.user.repo import UserWriteRepo, UserReadRepo
from bounded_contexts.user.schemas import UserCreate, UserUpdate, ResetPasswordRequest
from core.consts import DEMO_USER_EMAIL
from core.exceptions import AdminRequired, SuperAdminRequired
from core.services.auth import create_jwt_token, general_validade_token
from core.services.email import send_email
from core.services.password import verify_password, hash_password
from core.settings import FRONTEND_URL, ENV_CONFIG


def authenticate_user(email: str, password: str, session: Session) -> User:
    user = UserReadRepo(session=session).get_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        raise LoginUnauthorized()

    return user


def create_logged_user(user_id: UUID, is_demo_user: bool, session: Session) -> str:
    refresh_token = secrets.token_urlsafe(32)
    UserWriteRepo(session).create_logged_user(user_id, refresh_token, is_demo_user)
    return refresh_token


def delete_logged_user(refresh_token: str, session: Session) -> None:
    logged = UserReadRepo(session).get_logged_user_by_token(refresh_token)
    if not logged:
        return

    # Demo child user is deleted on logout
    user = logged.user
    created_by = (
        UserReadRepo(session).get_by_id(user.created_by) if user.created_by else None
    )
    if created_by and created_by.email == DEMO_USER_EMAIL:
        # Logged demo user will be deleted on cascade
        UserWriteRepo(session=session).delete(user)
        return

    UserWriteRepo(session).delete_logged_user(logged)


def get_logged_user_by_token(refresh_token: str, session: Session) -> LoggedUser | None:
    return UserReadRepo(session).get_logged_user_by_token(refresh_token)


def send_reset_password_email(email: str, session: Session) -> str:
    user = UserReadRepo(session).get_by_email(email)
    if not user:
        raise UserNotFound()

    token = create_jwt_token(
        data={
            "sub": str(user.id),
            "team_id": str(user.team_id),
        },
        expires_delta=timedelta(hours=1),
    )
    reset_link = f"{FRONTEND_URL}/reset-password?token={token}"

    if "test" not in ENV_CONFIG:
        send_email(
            to=email,
            subject="Redefinição de senha - Forquilha",
            body=f"{user.name}, uma solicitação de redefinição de senha foi solicitada. Caso você não tenha feito esta solicitação, ignore esse email.<br><br>Caso você tenha feito essa solicitação, clique no link abaixo para definir uma nova senha:<br><br><a href='{reset_link}'>Redefinir minha senha</a><br><br>",
        )

    return reset_link


def reset_password(reset_data: ResetPasswordRequest, session: Session) -> None:
    user_id = general_validade_token(reset_data.token)
    user = UserReadRepo(session).get_by_id(user_id)
    if not user:
        raise UserNotFound()

    user.hashed_password = hash_password(reset_data.new_password)
    UserWriteRepo(session).save(user, user.id)

    if "test" in ENV_CONFIG:
        return

    try:
        send_email(
            to=user.email,
            subject="Sua senha foi atualizada - Forquilha",
            body=f"Sua senha foi atualizada com sucesso. Caso você não tenha feito essa alteração, entre em contato com o suporte.",
        )
    except Exception as e:
        logger.exception(f"Error sending password reseted email: {e}")


def create_user(user_data: UserCreate, current_user: User, session: Session) -> User:
    if not TeamReadRepo(session=session).get_by_id(current_user.team_id):
        raise TeamNotFound()

    if UserReadRepo(session=session).get_by_email(user_data.email):
        raise EmailAlreadyInUse()

    if not current_user.is_super_admin and user_data.is_super_admin:
        raise SuperAdminRequired()

    if user_data.player_id and UserReadRepo(session=session).get_by_player_id(
        current_user.team_id, user_data.player_id
    ):
        raise PlayerAlreadyHasUser()

    hashed_password = hash_password(user_data.password)

    return UserWriteRepo(session=session).create(
        user_data, current_user, hashed_password
    )


def update_user(
    user_id: UUID, update_data: UserUpdate, session: Session, current_user: User
) -> User:
    user_to_update = UserReadRepo(session=session).get_by_id(user_id)
    if not user_to_update:
        raise UserNotFound()

    _validate_update_request(current_user, user_to_update, update_data)

    if update_data.email != user_to_update.email and UserReadRepo(
        session=session
    ).get_by_email(update_data.email):
        raise EmailAlreadyInUse()

    if (
        update_data.player_id
        and update_data.player_id != user_to_update.player_id
        and UserReadRepo(session=session).get_by_player_id(
            current_user.team_id, update_data.player_id
        )
    ):
        raise PlayerAlreadyHasUser()

    if all(
        [
            not update_data.password,
            user_to_update.name == update_data.name,
            user_to_update.email == update_data.email,
            user_to_update.player_id == update_data.player_id,
        ]
    ):
        return user_to_update

    return UserWriteRepo(session=session).update(
        user_to_update, update_data, current_user.id
    )


def _validate_update_request(
    current_user: User, user_to_update: User, update_data: UserUpdate
) -> None:
    if update_data.player_id and not current_user.has_admin_privileges:
        raise AdminRequired()

    if current_user.is_super_admin or current_user.id == user_to_update.id:
        return

    # Cannot update other users' passwords
    if update_data.password:
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


def get_users_by_name_in_and_permission_type(
    name_snippet: str, permission_type: UserPermissions, team_id: UUID, session: Session
) -> list[User]:
    if permission_type:
        is_admin = permission_type.has_admin_privileges
        return UserReadRepo(session=session).get_by_name_in_and_is_admin(
            name_snippet, is_admin, team_id
        )

    return UserReadRepo(session=session).get_by_name_in(name_snippet, team_id)


def get_users_by_email_in_and_permission_type(
    email_snippet: str,
    permission_type: UserPermissions | None,
    team_id: UUID,
    session: Session,
) -> list[User]:
    if permission_type:
        is_admin = permission_type.has_admin_privileges
        return UserReadRepo(session=session).get_by_email_in_and_is_admin(
            email_snippet, is_admin, team_id
        )

    return UserReadRepo(session=session).get_by_email_in(email_snippet, team_id)


def get_users_by_permission_type(
    permission_type: UserPermissions, team_id: UUID, session: Session
) -> list[User]:
    is_admin = permission_type.has_admin_privileges
    return UserReadRepo(session=session).get_by_is_admin(is_admin, team_id)


def delete_user(user_id: UUID, current_user: User, session: Session) -> None:
    user_to_delete = get_user_by_id(user_id, session)
    if not user_to_delete:
        raise UserNotFound()

    _validate_delete_request(current_user, user_to_delete)

    UserWriteRepo(session=session).delete(user_to_delete)


def _validate_delete_request(current_user: User, user_to_delete: User) -> None:
    if current_user.id == user_to_delete.id:
        raise CantDeleteYourself()

    if current_user.is_super_admin:
        return

    if not current_user.is_admin:
        raise AdminRequired()

    if user_to_delete.has_admin_privileges:
        raise CantUpdateAdminUser()


def clear_expired_logged_users(session: Session) -> int:
    return UserWriteRepo(session=session).clear_expired_logged_users()
