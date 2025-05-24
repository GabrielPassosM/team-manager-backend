from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserCreate, UserUpdate
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select

from core.services.password import hash_password
from libs.datetime import utcnow


class UserWriteRepo(BaseRepo):
    def save(self, user_data: UserCreate, team_id: UUID, hashed_password: str) -> User:
        user_data = user_data.model_dump()
        user_data["team_id"] = team_id
        user_data["hashed_password"] = hashed_password
        user_data.pop("password")

        user = User(**user_data)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def update(
        self, user: User, user_data: UserUpdate, current_user: User | UUID
    ) -> User:
        user_data = user_data.model_dump()
        password = user_data.pop("password")
        if password:
            user_data["hashed_password"] = hash_password(password)

        for key, value in user_data.items():
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

    def delete(self, user: User, current_user: User | UUID) -> None:
        user.deleted = True
        user.updated_at = utcnow()
        user.updated_by = (
            current_user.id if isinstance(current_user, User) else current_user
        )
        self.session.merge(user)
        self.session.commit()


class UserReadRepo(BaseRepo):
    def get_by_id(self, user_id: UUID | str) -> User:
        if isinstance(user_id, str):
            user_id = UUID(user_id)

        return self.session.exec(
            select(User).where(
                User.id == user_id,
                User.deleted == False,
            )
        ).first()

    def get_by_team_excluding_super_admin_and_current_user(
        self, team_id: UUID, current_user_id: UUID
    ) -> list[User]:
        return self.session.exec(
            select(User).where(
                User.team_id == team_id,
                User.id != current_user_id,
                User.is_super_admin == False,
                User.deleted == False,
            )
        ).all()

    def get_by_email(self, email: str) -> User:
        return self.session.exec(
            select(User).where(
                User.email == email,
                User.deleted == False,
            )
        ).first()
