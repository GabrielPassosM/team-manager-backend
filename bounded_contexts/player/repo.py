from uuid import UUID

from sqlmodel import select

from bounded_contexts.player.models import Player
from bounded_contexts.user.models import User
from bounded_contexts.player.schemas import PlayerCreate, PlayerUpdate, PlayerFilter
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


class PlayerReadRepo(BaseRepo):
    def get_all_excluding_current_player(
        self, team_id: UUID, current_player_id: UUID | None
    ) -> list[Player]:
        query = select(Player).where(
            Player.team_id == team_id,
            Player.deleted == False,
        )
        if current_player_id:
            query = query.where(Player.id != current_player_id)
        query = query.order_by(Player.name)

        return self.session.exec(query).all()

    def get_by_id(self, player_id: UUID) -> Player | None:
        return self.session.exec(
            select(Player).where(  # type: ignore
                Player.id == player_id,
                Player.deleted == False,
            )
        ).first()

    def get_by_filters(self, team_id: UUID, filter_data: PlayerFilter) -> list[Player]:
        query = select(Player).where(
            Player.team_id == team_id,
            Player.deleted == False,
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
