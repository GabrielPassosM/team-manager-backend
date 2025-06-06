from uuid import UUID

from sqlmodel import select

from bounded_contexts.player.models import Player
from bounded_contexts.player.schemas import PlayerCreate
from core.repo import BaseRepo


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
