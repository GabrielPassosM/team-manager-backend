from bounded_contexts.user.models import User
from bounded_contexts.user.schemas import UserCreate
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select


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

    def delete(self, user: User) -> None:
        user.deleted = True
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

    def get_by_team_id_excluding_super_admin(self, team_id: UUID) -> list[User]:
        return self.session.exec(
            select(User).where(
                User.team_id == team_id,
                User.deleted == False,
                User.is_super_admin == False,
            )
        ).all()

    def get_by_email(self, email: str) -> User:
        return self.session.exec(
            select(User).where(
                User.email == email,
                User.deleted == False,
            )
        ).first()
