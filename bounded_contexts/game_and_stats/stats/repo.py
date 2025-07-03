from uuid import UUID, uuid4

from sqlalchemy import delete
from sqlalchemy.orm import selectinload
from sqlmodel import select

from bounded_contexts.game_and_stats.exceptions import (
    StatPlayerNotInGamePlayers,
    InvalidYellowCardsQuantity,
)
from bounded_contexts.game_and_stats.game.schemas import (
    GoalAndAssist,
    PlayerAndQuantity,
)
from bounded_contexts.game_and_stats.models import GamePlayerStat, StatOptions
from core.repo import BaseRepo


class GamePlayerStatWriteRepo(BaseRepo):
    def create_goals_and_assists_without_commit(
        self,
        team_id: UUID,
        game_id: UUID,
        stats_data: list[GoalAndAssist],
        game_players_ids: list[UUID],
        current_user_id: UUID,
    ) -> None:
        stats = []
        for stat_data in stats_data:
            goal_player_id = stat_data.goal_player_id
            if goal_player_id and goal_player_id not in game_players_ids:
                raise StatPlayerNotInGamePlayers()

            goal_id = uuid4()
            stats.append(
                GamePlayerStat(
                    id=goal_id,
                    team_id=team_id,
                    game_id=game_id,
                    player_id=goal_player_id,
                    stat=StatOptions.GOAL,
                    quantity=1,
                    created_by=current_user_id,
                )
            )

            if stat_data.assist_player_id:
                stats.append(
                    GamePlayerStat(
                        team_id=team_id,
                        game_id=game_id,
                        player_id=stat_data.assist_player_id,
                        related_stat_id=goal_id,
                        stat=StatOptions.ASSIST,
                        quantity=1,
                        created_by=current_user_id,
                    )
                )
        self.session.add_all(stats)
        self.session.flush()

    def create_single_quantity_stats_without_commit(
        self,
        stat_type: StatOptions,
        team_id: UUID,
        game_id: UUID,
        player_ids: list[UUID],
        current_user_id: UUID,
        game_players_ids: list[UUID] = None,
    ) -> None:
        stats = []
        for player_id in player_ids:
            if game_players_ids and player_id not in game_players_ids:
                raise StatPlayerNotInGamePlayers()

            stats.append(
                GamePlayerStat(
                    team_id=team_id,
                    game_id=game_id,
                    player_id=player_id,
                    stat=stat_type,
                    quantity=1,
                    created_by=current_user_id,
                )
            )
        self.session.add_all(stats)
        self.session.flush()

    def create_stats_per_player_quantity_without_commit(
        self,
        stat_type: StatOptions,
        team_id: UUID,
        game_id: UUID,
        stats_data: list[PlayerAndQuantity],
        game_players_ids: list[UUID],
        current_user_id: UUID,
    ) -> None:
        stats = []
        for stat_data in stats_data:
            if stat_data.player_id not in game_players_ids:
                raise StatPlayerNotInGamePlayers()
            if stat_type == StatOptions.YELLOW_CARD and stat_data.quantity > 2:
                raise InvalidYellowCardsQuantity()

            stats.append(
                GamePlayerStat(
                    team_id=team_id,
                    game_id=game_id,
                    player_id=stat_data.player_id,
                    stat=stat_type,
                    quantity=stat_data.quantity,
                    created_by=current_user_id,
                )
            )

        self.session.add_all(stats)
        self.session.flush()

    def hard_delete_without_commit_by_game_id(self, game_id: UUID) -> None:
        self.session.exec(
            delete(GamePlayerStat).where(
                GamePlayerStat.game_id == game_id,
                GamePlayerStat.deleted == False,
            )
        )
        self.session.flush()


class GamePlayerStatReadRepo(BaseRepo):
    def get_by_game_id(self, game_id: UUID) -> list[GamePlayerStat]:
        return self.session.exec(
            select(GamePlayerStat)  # type: ignore
            .where(
                GamePlayerStat.game_id == game_id,
                GamePlayerStat.deleted == False,
            )
            .options(selectinload(GamePlayerStat.player))
        ).all()
