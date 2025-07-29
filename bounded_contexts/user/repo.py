from datetime import timedelta

from bounded_contexts.user.models import User
from bounded_contexts.user.logged_user.models import LoggedUser
from bounded_contexts.user.schemas import UserCreate, UserUpdate
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select

from core.services.password import hash_password
from core.settings import REFRESH_TOKEN_EXPIRE_DAYS
from libs.datetime import utcnow


class UserWriteRepo(BaseRepo):
    def create(
        self, user_data: UserCreate, current_user: User, hashed_password: str
    ) -> User:
        user_data = user_data.model_dump()
        user_data["team_id"] = current_user.team_id
        user_data["hashed_password"] = hashed_password
        user_data.pop("password")
        user_data["created_by"] = current_user.id

        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_logged_user(self, user_id: UUID, refresh_token: str) -> None:
        logged = LoggedUser(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.session.add(logged)
        self.session.commit()

    def update(
        self, user: User, update_data: UserUpdate, current_user: User | UUID
    ) -> User:
        update_data = update_data.model_dump()
        password = update_data.pop("password")
        if password:
            update_data["hashed_password"] = hash_password(password)

        for key, value in update_data.items():
            if key == "id":
                continue
            setattr(user, key, value)

        user.updated_at = utcnow()
        user.updated_by = (
            current_user.id if isinstance(current_user, User) else current_user
        )

        self.session.merge(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def save(self, user: User, current_user_id: UUID) -> None:
        user.updated_at = utcnow()
        user.updated_by = current_user_id
        self.session.merge(user)
        self.session.commit()

    def delete(self, user: User) -> None:
        # Hard delete to free the email for reuse (uniq in db)
        self.session.delete(user)
        self.session.commit()

    def delete_logged_user(self, logged: LoggedUser) -> None:
        self.session.delete(logged)
        self.session.commit()


class UserReadRepo(BaseRepo):
    def get_by_id(self, user_id: UUID | str) -> User:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        return self.session.exec(
            select(User).where(  # type: ignore
                User.id == user_id,
                User.deleted == False,
            )
        ).first()

    def get_logged_user_by_token(self, refresh_token: str) -> LoggedUser:
        return self.session.exec(
            select(LoggedUser).where(  # type: ignore
                LoggedUser.refresh_token == refresh_token
            )
        ).first()

    def get_by_team_excluding_super_admin_and_current_user(
        self, team_id: UUID, current_user_id: UUID
    ) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.team_id == team_id,
                User.id != current_user_id,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_email(self, email: str) -> User:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.email == email,
                User.deleted == False,
            )
        ).first()

    def get_by_name_in(self, name_snippet: str, team_id: UUID) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.name.ilike(f"%{name_snippet}%"),
                User.team_id == team_id,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_name_in_and_is_admin(
        self, name_snippet: str, is_admin: bool, team_id: UUID
    ) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.name.ilike(f"%{name_snippet}%"),
                User.team_id == team_id,
                User.is_admin == is_admin,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_email_in(self, email_snippet: str, team_id: UUID) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.email.ilike(f"%{email_snippet}%"),
                User.team_id == team_id,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_email_in_and_is_admin(
        self, email_snippet: str, is_admin: bool, team_id: UUID
    ) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.email.ilike(f"%{email_snippet}%"),
                User.team_id == team_id,
                User.is_admin == is_admin,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_is_admin(self, is_admin: bool, team_id: UUID) -> list[User]:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.team_id == team_id,
                User.is_admin == is_admin,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_team_super_user(self, team_id: UUID) -> User | None:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.team_id == team_id,
                User.is_super_admin == True,
                User.deleted == False,
            )
        ).first()

    def get_by_player_id(self, team_id: UUID, player_id: UUID) -> User | None:
        return self.session.exec(
            select(User).where(  # type: ignore
                User.team_id == team_id,
                User.player_id == player_id,
                User.deleted == False,
            )
        ).first()
