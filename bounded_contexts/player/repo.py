from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc, asc, case
from sqlmodel import select

from bounded_contexts.championship.repo import ChampionshipReadRepo
from bounded_contexts.game_and_stats.models import GamePlayerStat, Game, StatOptions
from bounded_contexts.player.models import Player
from bounded_contexts.user.models import User
from bounded_contexts.player.schemas import (
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerNameAndShirt,
    PlayersStatsFilter,
    PlayerResponse,
)
from core.repo import BaseRepo
from core.settings import FRIENDLY_CHAMPIONSHIP_NAME
from libs.datetime import utcnow, BRT, UTC


class PlayerWriteRepo(BaseRepo):
    def create(
        self, create_data: PlayerCreate, team_id: UUID, current_user_id: UUID
    ) -> Player:
        create_data = create_data.model_dump()
        create_data["team_id"] = team_id

        player = Player(**create_data)
        player.created_by = current_user_id
        self.session.add(player)
        self.session.commit()
        self.session.refresh(player)
        return player

    def update(
        self,
        player: Player,
        update_data: PlayerUpdate,
        current_user_id: UUID,
    ):
        for key, value in update_data.model_dump().items():
            if key == "id":
                continue
            if hasattr(player, key):
                setattr(player, key, value)

        player.updated_at = utcnow()
        player.updated_by = current_user_id

        self.session.merge(player)
        self.session.commit()
        self.session.refresh(player)
        return player

    def delete(self, player: Player, current_user: User) -> None:
        player.deleted = True
        player.updated_at = utcnow()
        player.updated_by = current_user.id
        self.session.merge(player)

        if current_user.player_id == player.id:
            current_user.player_id = None
            self.session.merge(current_user)

        self.session.commit()

    def delete_without_commit(self, player: Player, current_user_id: UUID) -> None:
        player.deleted = True
        player.updated_at = utcnow()
        player.updated_by = current_user_id
        self.session.merge(player)
        self.session.flush()

    def save(self, player: Player, current_user_id: UUID) -> None:
        player.updated_at = utcnow()
        player.updated_by = current_user_id
        self.session.merge(player)
        self.session.commit()


class PlayerReadRepo(BaseRepo):
    def get_by_team_id(self, team_id: UUID) -> list[Player]:
        return self.session.exec(
            (  # type: ignore
                select(Player)
                .where(
                    Player.team_id == team_id,
                    Player.deleted == False,
                )
                .options(selectinload(Player.game_player_stat))
            ).order_by(Player.name)
        ).all()

    def get_by_id(self, player_id: UUID) -> Player | None:
        return self.session.exec(
            select(Player).where(  # type: ignore
                Player.id == player_id,
                Player.deleted == False,
            )
        ).first()

    def get_by_ids(self, player_ids: list[UUID]) -> list[Player] | None:
        return self.session.exec(
            select(Player).where(  # type: ignore
                Player.id.in_(player_ids),
                Player.deleted == False,
            )
        ).all()

    def count_by_team_id(self, team_id: UUID) -> int:
        return self.session.exec(
            select(func.count()).where(  # type: ignore
                Player.team_id == team_id,
                Player.deleted == False,
            )
        ).one()

    def get_by_filters(self, team_id: UUID, filter_data: PlayerFilter) -> list[Player]:
        query = (
            select(Player)
            .where(
                Player.team_id == team_id,
                Player.deleted == False,
            )
            .options(selectinload(Player.game_player_stat))
        )

        if filter_data.name:
            query = query.where(Player.name.ilike(f"%{filter_data.name}%"))
        if filter_data.shirt_number:
            query = query.where(Player.shirt_number == filter_data.shirt_number)
        if filter_data.positions:
            positions_values = [position.value for position in filter_data.positions]
            query = query.where(Player.position.in_(positions_values))

        if filter_data.order_by:
            column_name = filter_data.order_by.rpartition("_")[0]
            direction = filter_data.order_by.rpartition("_")[-1]

            descending = False
            if direction == "desc":
                descending = True

            sortable_fields: dict[str, ColumnElement] = {  # type: ignore
                "name": Player.name,
                "shirt_number": Player.shirt_number,
            }

            field_to_order = sortable_fields[column_name]
            if descending:
                query = query.order_by(field_to_order.desc())
            else:
                query = query.order_by(field_to_order.asc())

        return self.session.exec(query).all()

    def get_all_without_user(self, team_id: UUID) -> list[Player]:
        return self.session.exec(  # type: ignore
            select(Player)
            .outerjoin(User, Player.id == User.player_id)
            .where(
                Player.team_id == team_id, Player.deleted == False, User.id.is_(None)
            )
        ).all()

    def get_all_players_only_name_and_shirt(
        self, team_id: UUID
    ) -> list[PlayerNameAndShirt]:
        result = (
            self.session.exec(
                select(Player.id, Player.name, Player.shirt_number)  # type: ignore
                .where(Player.team_id == team_id, Player.deleted == False)
                .order_by(Player.name.asc())
            )
            .mappings()
            .all()
        )
        return [PlayerNameAndShirt.model_validate(p) for p in result]

    def get_players_filtered_by_stats(
        self, filter_data: PlayersStatsFilter, team_id: UUID
    ) -> list[PlayerResponse]:
        sum_expressions_by_stat = {
            StatOptions.PLAYED: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.PLAYED,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "played_total",
            ],
            StatOptions.GOAL: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.GOAL,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "goals_total",
            ],
            StatOptions.ASSIST: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.ASSIST,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "assists_total",
            ],
            StatOptions.YELLOW_CARD: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.YELLOW_CARD,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "yellow_cards_total",
            ],
            StatOptions.RED_CARD: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.RED_CARD,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "red_cards_total",
            ],
            StatOptions.MVP: [
                func.sum(
                    case(
                        (
                            GamePlayerStat.stat == StatOptions.MVP,
                            GamePlayerStat.quantity,
                        ),
                        else_=0,
                    )
                ),
                "mvps_total",
            ],
        }

        stmt = (
            select(
                Player,
                sum_expressions_by_stat[StatOptions.PLAYED][0].label(
                    sum_expressions_by_stat[StatOptions.PLAYED][1]
                ),
                sum_expressions_by_stat[StatOptions.GOAL][0].label(
                    sum_expressions_by_stat[StatOptions.GOAL][1]
                ),
                sum_expressions_by_stat[StatOptions.ASSIST][0].label(
                    sum_expressions_by_stat[StatOptions.ASSIST][1]
                ),
                sum_expressions_by_stat[StatOptions.YELLOW_CARD][0].label(
                    sum_expressions_by_stat[StatOptions.YELLOW_CARD][1]
                ),
                sum_expressions_by_stat[StatOptions.RED_CARD][0].label(
                    sum_expressions_by_stat[StatOptions.RED_CARD][1]
                ),
                sum_expressions_by_stat[StatOptions.MVP][0].label(
                    sum_expressions_by_stat[StatOptions.MVP][1]
                ),
            )
            .join(GamePlayerStat, GamePlayerStat.player_id == Player.id)
            .join(Game, Game.id == GamePlayerStat.game_id)
            .where(
                GamePlayerStat.team_id == team_id,
                GamePlayerStat.deleted == False,
                GamePlayerStat.player_id.isnot(None),
            )
            .group_by(Player.id)
        )

        if filter_data.quantity_range:
            if filter_data.quantity_range.min is not None:
                stmt = stmt.having(
                    sum_expressions_by_stat[filter_data.stat_name][0]
                    >= filter_data.quantity_range.min
                )
            if filter_data.quantity_range.max is not None:
                stmt = stmt.having(
                    sum_expressions_by_stat[filter_data.stat_name][0]
                    <= filter_data.quantity_range.max
                )

        if filter_data.date_range:
            if filter_data.date_range.start is not None:
                start_local = datetime.combine(
                    filter_data.date_range.start, datetime.min.time(), tzinfo=BRT
                )
                start_utc = start_local.astimezone(UTC)
                stmt = stmt.where(Game.date_hour >= start_utc)
            if filter_data.date_range.end is not None:
                end_local = datetime.combine(
                    filter_data.date_range.end, datetime.max.time(), tzinfo=BRT
                )
                end_utc = end_local.astimezone(UTC)
                stmt = stmt.where(Game.date_hour <= end_utc)

        if filter_data.championships:
            stmt = stmt.where(Game.championship_id.in_(filter_data.championships))
        elif filter_data.exclude_friendly:
            friendly = ChampionshipReadRepo(self.session).get_by_name(
                FRIENDLY_CHAMPIONSHIP_NAME, team_id
            )
            stmt = stmt.where(Game.championship_id != friendly.id)

        if filter_data.stages:
            stages_values = [stg.value for stg in filter_data.stages]
            stmt = stmt.where(Game.stage.in_(stages_values))

        if filter_data.players:
            stmt = stmt.where(Player.id.in_(filter_data.players))

        if filter_data.player_positions:
            positions_values = [
                position.value for position in filter_data.player_positions
            ]
            stmt = stmt.where(Player.position.in_(positions_values))

        if filter_data.order_by:
            order_func = asc if filter_data.order_by == "asc" else desc
            order_tiebreaker = asc if filter_data.order_by == "desc" else desc
            stmt = stmt.order_by(
                order_func(sum_expressions_by_stat[filter_data.stat_name][1]),
                order_tiebreaker(sum_expressions_by_stat[StatOptions.PLAYED][1]),
                Player.name.asc(),
            )
        else:
            stmt = stmt.order_by(
                desc(sum_expressions_by_stat[filter_data.stat_name][1]),
                asc(sum_expressions_by_stat[StatOptions.PLAYED][1]),
                Player.name.asc(),
            )

        results = self.session.exec(stmt).all()

        response = []
        for player, played, goals, assists, yellows, reds, mvps in results:
            response.append(
                PlayerResponse(
                    id=player.id,
                    name=player.name,
                    image_url=player.image_url,
                    shirt_number=player.shirt_number,
                    position=player.position,
                    played=played or 0,
                    goals=goals or 0,
                    assists=assists or 0,
                    yellow_cards=yellows or 0,
                    red_cards=reds or 0,
                    mvps=mvps or 0,
                )
            )

        return response
