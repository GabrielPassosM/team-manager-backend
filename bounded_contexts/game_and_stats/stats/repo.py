from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import delete, func, desc, asc
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
from bounded_contexts.game_and_stats.models import GamePlayerStat, StatOptions, Game
from bounded_contexts.player.models import Player
from core.repo import BaseRepo
from libs.datetime import utcnow, current_month_range


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

            if not stat_data.ignore_goal:
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
        forced_quantity: int | None = None,
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
                    quantity=forced_quantity or 1,
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
        is_before_system: bool = False,
    ) -> None:
        stats = []
        for stat_data in stats_data:
            if stat_data.player_id not in game_players_ids:
                raise StatPlayerNotInGamePlayers()
            if (
                stat_type == StatOptions.YELLOW_CARD
                and stat_data.quantity > 2
                and not is_before_system
            ):
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

    def soft_delete_without_commit(
        self, game_stats: list[GamePlayerStat], current_user_id: UUID
    ) -> None:
        for stat in game_stats:
            stat.deleted = True
            stat.updated_at = utcnow()
            stat.updated_by = current_user_id
            self.session.merge(stat)
        self.session.flush()

    def reactivate_without_commit(
        self, game_stats: list[GamePlayerStat], current_user_id: UUID
    ) -> None:
        for stat in game_stats:
            stat.deleted = False
            stat.updated_at = utcnow()
            stat.updated_by = current_user_id
            self.session.merge(stat)
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

    def get_by_player(self, player_id: UUID) -> list[GamePlayerStat]:
        return self.session.exec(
            select(GamePlayerStat).where(  # type: ignore
                GamePlayerStat.player_id == player_id,
                GamePlayerStat.deleted == False,
            )
        ).all()

    def get_month_top_scorer(
        self, team_id: UUID
    ) -> tuple[Player | None, int | None, int | None]:
        interval = current_month_range()

        games_played_cte = (
            select(
                GamePlayerStat.player_id,
                func.count(GamePlayerStat.id).label("games_played"),
            )
            .join(Game, Game.id == GamePlayerStat.game_id)
            .where(
                Game.date_hour >= interval.start,
                Game.date_hour <= interval.end,
                GamePlayerStat.stat == StatOptions.PLAYED,
                GamePlayerStat.deleted == False,
                GamePlayerStat.player_id.isnot(None),
            )
            .group_by(GamePlayerStat.player_id)
            .cte("games_played_cte")
        )

        top_scorer_stmt = (
            select(
                Player,
                func.sum(GamePlayerStat.quantity).label("total_goals"),
                games_played_cte.c.games_played,
            )
            .join(GamePlayerStat, GamePlayerStat.player_id == Player.id)
            .join(Game, Game.id == GamePlayerStat.game_id)
            .join(games_played_cte, games_played_cte.c.player_id == Player.id)
            .where(
                GamePlayerStat.team_id == team_id,
                Game.date_hour >= interval.start,
                Game.date_hour <= interval.end,
                GamePlayerStat.stat == StatOptions.GOAL,
                GamePlayerStat.deleted == False,
                GamePlayerStat.player_id.isnot(None),
            )
            .group_by(Player.id, games_played_cte.c.games_played)
            .order_by(
                desc("total_goals"),
                asc(games_played_cte.c.games_played),
                Player.name.asc(),
            )
            .limit(1)
        )

        result = self.session.exec(top_scorer_stmt).first()
        if not result:
            return None, None, None

        player, goals, games_played = result
        if not goals:
            return None, None, None

        return player, goals, games_played

    def get_top_mvp_from_games(
        self, game_ids: list[UUID]
    ) -> tuple[Player | None, int | None]:
        result = self.session.exec(
            select(Player, func.sum(GamePlayerStat.quantity).label("total_mvp_points"))
            .join(GamePlayerStat, GamePlayerStat.player_id == Player.id)
            .where(
                GamePlayerStat.game_id.in_(game_ids),
                GamePlayerStat.stat == StatOptions.MVP,
                GamePlayerStat.deleted == False,
                GamePlayerStat.player_id.isnot(None),
            )
            .group_by(Player.id)
            .order_by(desc("total_mvp_points"))
            .limit(1)
        ).first()

        if not result:
            return None, None

        player, mvp_points = result
        return player, mvp_points
