from bounded_contexts.team.models import Team
from bounded_contexts.team.schemas import TeamCreate
from core.repo import BaseRepo
from libs.base_types.uuid import BaseUUID

from sqlmodel import select


class TeamWriteRepo(BaseRepo):
    def save(self, team_data: TeamCreate) -> Team:
        team = Team(**team_data.model_dump())
        self.session.add(team)
        self.session.commit()
        self.session.refresh(team)
        return team

    def delete(self, team: Team) -> None:
        team.deleted = True
        self.session.merge(team)
        self.session.commit()


class TeamReadRepo(BaseRepo):
    def get_by_id(self, team_id: BaseUUID) -> Team:
        return self.session.exec(
            select(Team).where(
                Team.id == team_id,
                Team.deleted == False,
            )
        ).first()
