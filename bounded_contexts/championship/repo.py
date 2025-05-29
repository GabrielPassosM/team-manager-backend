from datetime import date

from bounded_contexts.championship.models import Championship
from bounded_contexts.championship.schemas import ChampionshipCreate, ChampionshipUpdate
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select, desc, and_, or_

from libs.datetime import brasilia_now, utcnow


class ChampionshipWriteRepo(BaseRepo):
    def save(
        self, create_data: ChampionshipCreate, team_id: UUID, current_user_id: UUID
    ) -> Championship:
        create_data = create_data.model_dump()
        create_data["team_id"] = team_id

        championship = Championship(**create_data)
        championship.created_by = current_user_id
        self.session.add(championship)
        self.session.commit()
        self.session.refresh(championship)
        return championship

    def update(
        self,
        championship: Championship,
        update_data: ChampionshipUpdate,
        current_user_id: UUID,
    ):
        for key, value in update_data.model_dump().items():
            if key == "id":
                continue
            setattr(championship, key, value)

        championship.updated_at = utcnow()
        championship.updated_by = current_user_id

        self.session.merge(championship)
        self.session.commit()
        self.session.refresh(championship)
        return championship

    def delete(self, championship: Championship, current_user_id: UUID):
        championship.deleted = True
        championship.updated_at = utcnow()
        championship.updated_by = current_user_id
        self.session.merge(championship)
        self.session.commit()


class ChampionshipReadRepo(BaseRepo):

    @classmethod
    def query_in_progress(cls, team_id: UUID, today: date = None) -> select:
        if not today:
            # defaulting on method's signature doesn't work with time_machine tests
            today = brasilia_now().date()
        return (
            select(Championship)
            .where(
                and_(
                    Championship.team_id == team_id,
                    Championship.deleted == False,
                    Championship.start_date <= today,
                    or_(Championship.end_date == None, Championship.end_date >= today),
                )
            )
            .order_by(desc(Championship.start_date))
        )

    @classmethod
    def query_upcoming(cls, team_id: UUID, today: date = None) -> select:
        if not today:
            # defaulting on method's signature doesn't work with time_machine tests
            today = brasilia_now().date()
        return (
            select(Championship)
            .where(
                and_(
                    Championship.team_id == team_id,
                    Championship.deleted == False,
                    Championship.start_date > today,
                )
            )
            .order_by(desc(Championship.start_date))
        )

    @classmethod
    def query_finished(cls, team_id: UUID, today: date = None) -> select:
        if not today:
            # defaulting on method's signature doesn't work with time_machine tests
            today = brasilia_now().date()
        return (
            select(Championship)
            .where(
                and_(
                    Championship.team_id == team_id,
                    Championship.deleted == False,
                    Championship.end_date < today,
                )
            )
            .order_by(desc(Championship.start_date))
        )

    def get_by_id(self, champ_id: UUID | str) -> Championship:
        if isinstance(champ_id, str):
            champ_id = UUID(champ_id)

        return self.session.exec(
            select(Championship).where(  # type: ignore
                Championship.id == champ_id,
                Championship.deleted == False,
            )
        ).first()

    def get_by_name(self, name: str, team_id: UUID) -> Championship | None:
        return self.session.exec(
            select(Championship).where(  # type: ignore
                Championship.name == name,
                Championship.team_id == team_id,
                Championship.deleted == False,
            )
        ).first()

    def get_all_order_by_status_and_start_date(
        self, team_id: UUID
    ) -> list[Championship]:
        in_progress_query = self.query_in_progress(team_id)
        upcoming_query = self.query_upcoming(team_id)
        finished_query = self.query_finished(team_id)

        return (
            self.session.exec(in_progress_query).all()
            + self.session.exec(upcoming_query).all()
            + self.session.exec(finished_query).all()
        )
