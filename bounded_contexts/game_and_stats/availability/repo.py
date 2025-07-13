from uuid import UUID

from sqlmodel import select
from sqlalchemy import func

from bounded_contexts.game_and_stats.availability.schemas import (
    GamePlayerAvailabilityCreate,
    GamePlayerAvailabilityUpdate,
)
from bounded_contexts.game_and_stats.models import (
    GamePlayerAvailability,
    AvailabilityStatus,
)
from core.repo import BaseRepo
from libs.datetime import utcnow


class AvailabilityWriteRepo(BaseRepo):
    def create(
        self,
        create_data: GamePlayerAvailabilityCreate,
        team_id: UUID,
        player_id: UUID,
        current_user_id: UUID,
    ) -> GamePlayerAvailability:
        create_data = create_data.model_dump()
        create_data["team_id"] = team_id
        create_data["player_id"] = player_id

        availability = GamePlayerAvailability(**create_data)
        availability.created_by = current_user_id
        self.session.add(availability)
        self.session.commit()
        self.session.refresh(availability)
        return availability

    def update(
        self,
        availability: GamePlayerAvailability,
        update_data: GamePlayerAvailabilityUpdate,
        current_user_id: UUID,
    ):
        for key, value in update_data.model_dump().items():
            if key == "id":
                continue
            setattr(availability, key, value)

        availability.updated_at = utcnow()
        availability.updated_by = current_user_id

        self.session.merge(availability)
        self.session.commit()
        self.session.refresh(availability)
        return availability

    def delete(
        self, availability: GamePlayerAvailability, current_user_id: UUID
    ) -> None:
        availability.deleted = True
        availability.updated_at = utcnow()
        availability.updated_by = current_user_id
        self.session.merge(availability)
        self.session.commit()

    def delete_many_without_commit(
        self, availabilities: list[GamePlayerAvailability], current_user_id: UUID
    ) -> None:
        for availability in availabilities:
            availability.deleted = True
            availability.updated_at = utcnow()
            availability.updated_by = current_user_id
            self.session.merge(availability)
        self.session.flush()

    def reactivate(
        self,
        availability: GamePlayerAvailability,
        new_status: AvailabilityStatus,
        current_user_id: UUID,
    ) -> None:
        availability.deleted = False
        availability.status = new_status
        availability.updated_at = utcnow()
        availability.updated_by = current_user_id
        self.session.merge(availability)
        self.session.commit()


class AvailabilityReadRepo(BaseRepo):
    def get_by_game_id(self, game_id: UUID) -> list[GamePlayerAvailability]:
        return self.session.exec(
            select(GamePlayerAvailability).where(  # type: ignore
                GamePlayerAvailability.game_id == game_id,
                GamePlayerAvailability.deleted == False,
            )
        ).all()

    def get_by_game_and_player(
        self, game_id: UUID, player_id: UUID, deleted: bool = False
    ) -> GamePlayerAvailability:
        return self.session.exec(
            select(GamePlayerAvailability).where(  # type: ignore
                GamePlayerAvailability.game_id == game_id,
                GamePlayerAvailability.player_id == player_id,
                GamePlayerAvailability.deleted == deleted,
            )
        ).first()

    def count_confirmed_players_by_game(self, game_id: UUID) -> int:
        return self.session.exec(
            select(func.count()).where(  # type: ignore
                GamePlayerAvailability.game_id == game_id,
                GamePlayerAvailability.status == AvailabilityStatus.AVAILABLE,
                GamePlayerAvailability.deleted == False,
            )
        ).one()
