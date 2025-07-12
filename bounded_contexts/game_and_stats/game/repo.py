from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from bounded_contexts.game_and_stats.models import Game
from bounded_contexts.game_and_stats.game.schemas import (
    GameCreate,
    GameInfoIn,
    GameFilter,
)
from core.repo import BaseRepo
from libs.datetime import utcnow


class GameWriteRepo(BaseRepo):
    def create_without_commit(
        self, create_data: GameCreate, team_id: UUID, current_user_id: UUID
    ) -> Game:
        create_data = create_data.model_dump()
        create_data["team_id"] = team_id

        game = Game(**create_data)
        game.created_by = current_user_id
        self.session.add(game)
        self.session.flush()
        self.session.refresh(game)
        return game

    def update_without_commit(
        self, game: Game, update_data: GameInfoIn, current_user_id: UUID
    ):
        for key, value in update_data.model_dump().items():
            if key == "id":
                continue
            setattr(game, key, value)

        game.updated_at = utcnow()
        game.updated_by = current_user_id
        self.session.merge(game)
        self.session.flush()

    def delete_without_commit(self, game: Game, current_user_id: UUID):
        game.deleted = True
        game.updated_at = utcnow()
        game.updated_by = current_user_id
        self.session.merge(game)
        self.session.flush()

    def reactivate_without_commit(self, game: Game, current_user_id: UUID):
        game.deleted = False
        game.updated_at = utcnow()
        game.updated_by = current_user_id
        self.session.merge(game)
        self.session.flush()


class GameReadRepo(BaseRepo):

    @classmethod
    def _base_get_paginated_query(
        cls, team_id: UUID, offset: int, limit: int
    ) -> select:
        return (
            select(Game)
            .where(
                Game.team_id == team_id,
                Game.deleted == False,
            )
            .options(selectinload(Game.championship))
            .offset(offset)
            .limit(limit)
        )

    def get_by_id(self, game_id: UUID, deleted: bool = False) -> Game | None:
        return self.session.exec(
            select(Game).where(  # type: ignore
                Game.id == game_id, Game.deleted == deleted
            )
        ).first()

    def get_all_paginated(
        self, team_id: UUID, limit: int, offset: int
    ) -> tuple[list[Game], int]:
        query = self._base_get_paginated_query(team_id, offset, limit)
        query = query.order_by(Game.date_hour.desc())
        games = self.session.exec(query).all()

        count = self.session.exec(
            select(func.count()).where(  # type: ignore
                Game.team_id == team_id,
                Game.deleted == False,
            )
        ).one()
        return games, count

    def get_by_filters_paginated(
        self, team_id: UUID, filter_data: GameFilter, limit: int, offset: int
    ) -> tuple[list[Game], int]:
        query = self._base_get_paginated_query(team_id, offset, limit)

        count_query = select(func.count()).where(
            Game.team_id == team_id,
            Game.deleted == False,
        )

        if filter_data.championship_id:
            query = query.where(Game.championship_id == filter_data.championship_id)
            count_query = count_query.where(
                Game.championship_id == filter_data.championship_id
            )
        if filter_data.adversary:
            query = query.where(Game.adversary.ilike(f"%{filter_data.adversary}%"))
            count_query = count_query.where(
                Game.adversary.ilike(f"%{filter_data.adversary}%")
            )
        if filter_data.date_hour_from:
            query = query.where(Game.date_hour >= filter_data.date_hour_from)
            count_query = count_query.where(
                Game.date_hour >= filter_data.date_hour_from
            )
        if filter_data.date_hour_to:
            query = query.where(Game.date_hour <= filter_data.date_hour_to)
            count_query = count_query.where(Game.date_hour <= filter_data.date_hour_to)
        if filter_data.round:
            query = query.where(Game.round == filter_data.round)
            count_query = count_query.where(Game.round == filter_data.round)
        if filter_data.stages:
            stages_values = [stg.value for stg in filter_data.stages]
            query = query.where(Game.stage.in_(stages_values))
            count_query = count_query.where(Game.stage.in_(stages_values))
        if filter_data.is_home is not None:
            query = query.where(Game.is_home == filter_data.is_home)
            count_query = count_query.where(Game.is_home == filter_data.is_home)
        if filter_data.is_wo is not None:
            query = query.where(Game.is_wo == filter_data.is_wo)
            count_query = count_query.where(Game.is_wo == filter_data.is_wo)
        if filter_data.team_score_from is not None:
            query = query.where(Game.team_score != None)
            query = query.where(Game.team_score >= filter_data.team_score_from)
            count_query = count_query.where(Game.team_score != None)
            count_query = count_query.where(
                Game.team_score >= filter_data.team_score_from
            )
        if filter_data.team_score_to is not None:
            query = query.where(Game.team_score != None)
            query = query.where(Game.team_score <= filter_data.team_score_to)
            count_query = count_query.where(Game.team_score != None)
            count_query = count_query.where(
                Game.team_score <= filter_data.team_score_to
            )
        if filter_data.adversary_score_from is not None:
            query = query.where(Game.adversary_score != None)
            query = query.where(
                Game.adversary_score >= filter_data.adversary_score_from
            )
            count_query = count_query.where(Game.adversary_score != None)
            count_query = count_query.where(
                Game.adversary_score >= filter_data.adversary_score_from
            )
        if filter_data.adversary_score_to is not None:
            query = query.where(Game.adversary_score != None)
            query = query.where(Game.adversary_score <= filter_data.adversary_score_to)
            count_query = count_query.where(Game.adversary_score != None)
            count_query = count_query.where(
                Game.adversary_score <= filter_data.adversary_score_to
            )
        if filter_data.has_penalty_score is not None:
            if filter_data.has_penalty_score:
                query = query.where(Game.team_penalty_score != None)
                count_query = count_query.where(Game.team_penalty_score != None)
            else:
                query = query.where(Game.team_penalty_score == None)
                count_query = count_query.where(Game.team_penalty_score == None)

        if not filter_data.order_by:
            query = query.order_by(Game.date_hour.desc())
        else:
            column_name = filter_data.order_by.rpartition("_")[0]
            direction = filter_data.order_by.rpartition("_")[-1]

            descending = False
            if direction == "desc":
                descending = True

            sortable_fields = {
                "date_hour": Game.date_hour,
                "team_score": Game.team_score,
                "adversary_score": Game.adversary_score,
            }

            field_to_order = sortable_fields[column_name]

            if column_name == "team_score":
                query = query.where(Game.team_score != None)
                count_query = count_query.where(Game.team_score != None)
            elif column_name == "adversary_score":
                query = query.where(Game.adversary_score != None)
                count_query = count_query.where(Game.adversary_score != None)

            if descending:
                query = query.order_by(field_to_order.desc())
            else:
                query = query.order_by(field_to_order.asc())

        games = self.session.exec(query).all()
        total_games_for_filters = self.session.exec(count_query).one()

        return games, total_games_for_filters

    def count_games_by_championship(self, champ_id: UUID) -> int:
        return self.session.exec(
            select(func.count()).where(  # type: ignore
                Game.championship_id == champ_id,
                Game.deleted == False,
            )
        ).one()
