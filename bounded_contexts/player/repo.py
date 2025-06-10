from uuid import UUID

from sqlmodel import select

from bounded_contexts.player.models import Player
from bounded_contexts.player.schemas import PlayerCreate, PlayerUpdate
from core.repo import BaseRepo
from libs.datetime import utcnow


class PlayerWriteRepo(BaseRepo):
    def save(
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

    def delete(self, player: Player, current_user_id: UUID) -> None:
        player.deleted = True
        player.updated_at = utcnow()
        player.updated_by = current_user_id
        self.session.merge(player)
        self.session.commit()


class PlayerReadRepo(BaseRepo):
    def get_all(self, team_id: UUID) -> list[Player]:
        return self.session.exec(
            select(Player)
            .where(  # type: ignore
                Player.team_id == team_id,
                Player.deleted == False,
            )
            .order_by(Player.name)
        ).all()

    def get_by_id(self, player_id: UUID) -> Player | None:
        return self.session.exec(
            select(Player).where(  # type: ignore
                Player.id == player_id,
                Player.deleted == False,
            )
        ).first()
