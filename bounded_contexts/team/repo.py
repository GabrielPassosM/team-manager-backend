from bounded_contexts.team.models import Team, IntentionToSubscribe
from bounded_contexts.team.schemas import (
    TeamCreate,
    TeamUpdate,
    IntentionToSubscribeCreate,
)
from bounded_contexts.user.models import User
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select

from libs.datetime import utcnow


class TeamWriteRepo(BaseRepo):
    def create(self, team_data: TeamCreate) -> Team:
        team = Team(**team_data.model_dump())
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)
        return team

    def delete(self, team: Team) -> None:
        team.deleted = True
        self.session.merge(team)
        self.session.commit()

    def update(
        self, team: Team, team_data: TeamUpdate, current_user: User | UUID
    ) -> Team:
        for key, value in team_data.model_dump().items():
            if key == "id":
                continue
            setattr(team, key, value)
        team.updated_at = utcnow()
        team.updated_by = (
            current_user.id if isinstance(current_user, User) else current_user
        )

        self.session.merge(team)
        self.session.commit()
        self.session.refresh(team)
        return team


class TeamReadRepo(BaseRepo):
    def get_by_id(self, team_id: UUID) -> Team:
        return self.session.exec(
            select(Team).where(  # type: ignore
                Team.id == team_id,
                Team.deleted == False,
            )
        ).first()


class IntentionToSubscribeWriteRepo(BaseRepo):
    def create(self, intention_data: IntentionToSubscribeCreate) -> None:
        intention = IntentionToSubscribe(**intention_data.model_dump())
        self.session.add(intention)
        self.session.commit()

    def delete(self, intention: IntentionToSubscribe) -> None:
        self.session.delete(intention)
        self.session.commit()


class IntentionToSubscribeReadRepo(BaseRepo):
    def get_by_email(self, email: str) -> IntentionToSubscribe | None:
        return self.session.exec(
            select(IntentionToSubscribe).where(  # type: ignore
                IntentionToSubscribe.user_email == email,
                IntentionToSubscribe.deleted == False,
            )
        ).first()
