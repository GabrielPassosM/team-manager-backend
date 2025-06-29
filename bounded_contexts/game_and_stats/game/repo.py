from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import selectinload
from sqlmodel import select

from bounded_contexts.game_and_stats.models import Game
from bounded_contexts.game_and_stats.game.schemas import GameCreate
from core.repo import BaseRepo


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


class GameReadRepo(BaseRepo):
    def get_all_paginated(
        self, team_id: UUID, limit: int, offset: int
    ) -> list[Game] | None:
        return self.session.exec(
            select(Game)
            .where(  # type: ignore
                Game.team_id == team_id,
                Game.deleted == False,
            )
            .options(selectinload(Game.championship))
            .order_by(Game.date_hour.desc())
            .offset(offset)
            .limit(limit)
        ).all()

    def count_all(self, team_id: UUID) -> int:
        return self.session.exec(
            select(func.count()).where(  # type: ignore
                Game.team_id == team_id,
                Game.deleted == False,
            )
        ).one()
