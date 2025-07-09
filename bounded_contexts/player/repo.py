from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import select

from bounded_contexts.player.models import Player
from bounded_contexts.user.models import User
from bounded_contexts.player.schemas import (
    PlayerCreate,
    PlayerUpdate,
    PlayerFilter,
    PlayerNameAndShirt,
)
from core.repo import BaseRepo
from libs.datetime import utcnow


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
