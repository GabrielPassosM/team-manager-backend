from datetime import date

from sqlalchemy import ColumnElement, delete

from bounded_contexts.championship.models import (
    Championship,
    ChampionshipFormats,
    ChampionshipStatus,
)
from bounded_contexts.championship.schemas import (
    ChampionshipCreate,
    ChampionshipUpdate,
    ChampionshipFilter,
)
from core.repo import BaseRepo

from uuid import UUID
from sqlmodel import select, desc, and_, or_, asc

from libs.datetime import brasilia_now, utcnow


class ChampionshipWriteRepo(BaseRepo):
    def create(
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

    def hard_delete_all_by_team_id(self, team_id: UUID) -> None:
        self.session.exec(
            delete(Championship).where(Championship.team_id == team_id)  # type: ignore
        )
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
            .order_by(asc(Championship.start_date))
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

    def get_by_filters(
        self, team_id: UUID, filters: ChampionshipFilter
    ) -> list[Championship]:
        query = select(Championship).where(
            Championship.team_id == team_id,
            Championship.deleted == False,
        )

        if filters.status:
            today = brasilia_now().date()
            status_conditions = []
            if ChampionshipStatus.NAO_INICIADO in filters.status:
                status_conditions.append(Championship.start_date > today)
            if ChampionshipStatus.FINALIZADO in filters.status:
                status_conditions.append(
                    (Championship.end_date != None) & (Championship.end_date < today)
                )
            if ChampionshipStatus.EM_ANDAMENTO in filters.status:
                condition_em_andamento = (Championship.start_date <= today) & (
                    (Championship.end_date == None) | (Championship.end_date >= today)
                )
                status_conditions.append(condition_em_andamento)
            if status_conditions:
                query = query.where(or_(*status_conditions))

        if filters.name:
            query = query.where(Championship.name.ilike(f"%{filters.name}%"))
        if filters.start_date_from:
            query = query.where(Championship.start_date >= filters.start_date_from)
        if filters.start_date_to:
            query = query.where(Championship.start_date <= filters.start_date_to)
        if filters.end_date_from:
            query = query.where(Championship.end_date != None)
            query = query.where(Championship.end_date >= filters.end_date_from)
        if filters.end_date_to:
            query = query.where(Championship.end_date != None)
            query = query.where(Championship.end_date <= filters.end_date_to)

        if filters.format:
            if filters.format == ChampionshipFormats.LEAGUE:
                query = query.where(Championship.is_league_format == True)
                if filters.final_position_from:
                    query = query.where(Championship.final_position != None)
                    query = query.where(
                        Championship.final_position >= filters.final_position_from
                    )
                if filters.final_position_to:
                    query = query.where(Championship.final_position != None)
                    query = query.where(
                        Championship.final_position <= filters.final_position_to
                    )

            elif filters.format == ChampionshipFormats.KNOCKOUT:
                query = query.where(Championship.is_league_format == False)
                if filters.final_stages:
                    final_stage_values = [stage.value for stage in filters.final_stages]
                    query = query.where(
                        Championship.final_stage.in_(final_stage_values)
                    )

        if filters.order_by:
            column_name = filters.order_by.rpartition("_")[0]
            direction = filters.order_by.rpartition("_")[-1]

            descending = False
            if direction == "desc":
                descending = True

            sortable_fields: dict[str, ColumnElement] = {  # type: ignore
                "start_date": Championship.start_date,
                "end_date": Championship.end_date,
            }

            field_to_order = sortable_fields[column_name]
            if descending:
                query = query.order_by(field_to_order.desc())
            else:
                query = query.order_by(field_to_order.asc())

        return self.session.exec(query).all()
